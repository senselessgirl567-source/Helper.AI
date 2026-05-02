import os
import urllib.parse
import requests


def _get_groq_base_url() -> str:
    project_id = os.environ.get('GROQ_PROJECT_ID')
    dataset = os.environ.get('GROQ_DATASET', 'production')
    if not project_id:
        raise RuntimeError('GROQ_PROJECT_ID environment variable is required.')
    return f'https://{project_id}.api.sanity.io/v1/data/query/{dataset}'


def groq_fetch(query: str):
    if not query or not isinstance(query, str):
        raise ValueError('GROQ query must be a non-empty string.')

    base_url = _get_groq_base_url()
    params = {'query': query}
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    token = os.environ.get('GROQ_API_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(base_url, headers=headers, params=params, timeout=15)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f'GROQ request failed: {response.status_code} {response.text}') from exc

    payload = response.json()
    if 'result' not in payload:
        raise RuntimeError('Unexpected GROQ response format: missing result field.')
    return payload['result']
