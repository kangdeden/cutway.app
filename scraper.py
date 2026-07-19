import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Configuration
START_URL = "https://cutway.app"
OUTPUT_FILE = "links.txt"


def is_valid_subpage(url, base_domain):
    """Ensure the link stays within the same website and isn't a file asset."""
    parsed = urlparse(url)

    # Check if it belongs to the same domain
    if parsed.netloc != base_domain:
        return False

    # Avoid images, CSS, or documents
    if any(url.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".css", ".js"]):
        return False

    return True


def deep_crawl():
    base_domain = urlparse(START_URL).netloc
    pages_to_visit = {START_URL, urljoin(START_URL, "/blog")}  # Explicitly include homepage and blog index
    visited_pages = set()
    all_discovered_links = set()

    # Crawl up to 15 internal pages to find all possible hyperlinks
    max_pages = 15

    while pages_to_visit and len(visited_pages) < max_pages:
        current_url = pages_to_visit.pop()

        if current_url in visited_pages:
            continue

        print(f"Scanning page: {current_url}")
        visited_pages.add(current_url)

        try:
            response = requests.get(current_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                # Resolve relative pathways to full URLs
                full_url = urljoin(current_url, href).split("#")[0].rstrip("/")

                if full_url.startswith("http"):
                    all_discovered_links.add(full_url)

                    # If it's a subpage of our site, add it to our queue to scan next
                    if is_valid_subpage(full_url, base_domain) and full_url not in visited_pages:
                        pages_to_visit.add(full_url)

        except Exception as e:
            print(f"Failed to parse {current_url}: {e}")

    return all_discovered_links


def update_file(new_links):
    existing_links = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            existing_links = set(line.strip() for line in f)

    all_links = existing_links.union(new_links)

    with open(OUTPUT_FILE, "w") as f:
        for link in sorted(all_links):
            f.write(f"{link}\n")

    print(f"Crawl completed. Saved {len(all_links)} total unique links.")


if __name__ == "__main__":
    links = deep_crawl()
    if links:
        update_file(links)
