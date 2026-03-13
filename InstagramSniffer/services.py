import logging
from curl_cffi import requests

logger = logging.getLogger(__name__)

IG_API_URL = "https://www.instagram.com/api/v1/users/web_profile_info/"
IG_HEADERS = {"X-IG-App-ID": "936619743392459"}


def _fetch_user_data(username):
    """Fetch raw user data from Instagram API. Returns (user_data, error_dict)."""
    url = f"{IG_API_URL}?username={username}"
    try:
        response = requests.get(url, headers=IG_HEADERS, timeout=30)
    except Exception as e:
        logger.error("Instagram API request failed: %s", e)
        return None, {
            "success": False,
            "error": "Error de conexión con Instagram. Intenta de nuevo más tarde.",
        }

    if response.status_code == 404:
        return None, {"success": False, "error": "Usuario no encontrado."}
    if response.status_code == 429:
        return None, {
            "success": False,
            "error": "Instagram ha limitado las solicitudes desde tu IP. Intenta de nuevo más tarde.",
        }
    if response.status_code != 200:
        return None, {
            "success": False,
            "error": f"Error de Instagram (código {response.status_code}).",
        }

    try:
        user_data = response.json()["data"]["user"]
    except (KeyError, ValueError) as e:
        logger.error("Failed to parse Instagram response: %s", e)
        return None, {
            "success": False,
            "error": "No se pudo interpretar la respuesta de Instagram.",
        }

    return user_data, None


def fetch_collaborated_posts(username):
    """Fetch collaborated posts from a private Instagram account.

    Returns a dict with keys: success, error, is_private, username, posts.
    """
    user_data, error = _fetch_user_data(username)
    if error:
        return error

    is_private = user_data.get("is_private", False)
    edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])

    posts = []
    for i, edge in enumerate(edges, 1):
        node = edge["node"]
        shortcode = node["shortcode"]
        is_video = node.get("is_video", False)
        owner = node.get("owner", {}).get("username", username)

        if is_video:
            post_url = f"https://www.instagram.com/{owner}/reel/{shortcode}"
            post_type = "video"
        else:
            post_url = f"https://www.instagram.com/{owner}/p/{shortcode}"
            post_type = "image"

        collaborators = []
        for collab_edge in node.get("edge_media_to_tagged_user", {}).get("edges", []):
            collab_username = collab_edge.get("node", {}).get("user", {}).get("username")
            if collab_username:
                collaborators.append(collab_username)

        posts.append({
            "index": i,
            "type": post_type,
            "url": post_url,
            "shortcode": shortcode,
            "owner": owner,
            "collaborators": collaborators,
        })

    return {
        "success": True,
        "error": None,
        "is_private": is_private,
        "username": username,
        "posts": posts,
    }


def fetch_media_info(post_url):
    """Extract direct media URL from an Instagram post URL.

    Returns a dict with keys: success, error, media_url, is_video, filename.
    """
    parts = post_url.rstrip("/").split("/")

    # Validate URL structure: https://www.instagram.com/{user}/(p|reel)/{shortcode}
    try:
        p_or_reel_idx = None
        for idx, part in enumerate(parts):
            if part in ("p", "reel"):
                p_or_reel_idx = idx
                break

        if p_or_reel_idx is None or p_or_reel_idx < 1 or p_or_reel_idx + 1 >= len(parts):
            raise ValueError("Invalid URL structure")

        post_type = parts[p_or_reel_idx]
        user_name = parts[p_or_reel_idx - 1]
        shortcode = parts[p_or_reel_idx + 1]
    except (ValueError, IndexError):
        return {
            "success": False,
            "error": "Formato de URL inválido. Usa: https://www.instagram.com/usuario/p/CODIGO/ o .../reel/CODIGO/",
        }

    user_data, error = _fetch_user_data(user_name)
    if error:
        return error

    edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])

    for edge in edges:
        node = edge["node"]
        if node["shortcode"] == shortcode:
            is_video = node.get("is_video", False)
            if is_video:
                media_url = node.get("video_url")
            else:
                media_url = node.get("display_url")

            if not media_url:
                return {
                    "success": False,
                    "error": "No se encontró la URL del medio en la publicación.",
                }

            ext = ".mp4" if is_video else ".png"
            safe_shortcode = shortcode.replace("-", "")[:10]
            filename = f"{user_name}-{post_type}-{safe_shortcode}{ext}"

            return {
                "success": True,
                "error": None,
                "media_url": media_url,
                "is_video": is_video,
                "filename": filename,
            }

    return {
        "success": False,
        "error": "No se encontró la publicación en el perfil del usuario.",
    }
