import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os
from collections import OrderedDict

talent_url_pattern = re.compile(
    r"https://hololive\.hololivepro\.com/en/talents/([^/\s?&]+)"
)


def scrape_hololive_talents_links():
    """Scrape all talent links from Hololive's talents page"""

    # Send GET request to the page
    url = "https://hololive.hololivepro.com/en/talents"
    response = requests.get(url)

    # Check if request was successful
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all links on the page
    links = soup.find_all("a", href=True)

    # Filter links that start with the talent URL pattern
    talent_links = []
    base_url = "https://hololive.hololivepro.com/en/talents/"

    for link in links:
        href = link["href"]
        # Check if the link starts with the base talent URL
        match = talent_url_pattern.search(href)
        if match:
            name = match.group(1)
            talent_links.append((name, href))

    return talent_links


def scrape_talent_socials(soup, out_dict):
    """Scrape social media links from a talent's profile page"""

    sns_ul = soup.find("ul", class_="t_sns")

    if not sns_ul:
        return

    li_elements = sns_ul.find_all("li")

    # Create dictionary from a elements
    for li in li_elements:
        a_element = li.find("a")
        if a_element and a_element.get("href"):
            text = a_element.get_text(strip=True)
            href = a_element["href"]
            out_dict[text] = href


def scrape_talent_gen(soup, out_dict):
    """Scrape generation info from a talent's profile page"""
    # Find the element with class "breadcrumb"
    breadcrumb_element = soup.find(class_="breadcrumb")

    if not breadcrumb_element:
        return

    # Find all span elements with property="itemListElement"
    spans = breadcrumb_element.find_all("span", property="itemListElement")

    # Extract text from each span (including text inside <a> tags)
    breadcrumb_texts = []
    for span in spans:
        # Get all text content from the span, including nested <a> tags
        text = span.get_text(strip=True)
        if text:
            breadcrumb_texts.append(text)

    out_dict["group"] = "/".join(breadcrumb_texts[1:-1])


def scrape_talent_name(soup, out_dict):

    bg_box = soup.find(class_="bg_box")

    if not bg_box:
        return

    h1_element = bg_box.find("h1")

    if not h1_element:
        return

    # Get text that is directly under the <h1> (not nested in child elements)
    # This approach gets only direct text nodes, excluding any text from nested tags
    for child in h1_element.children:
        if isinstance(child, str):
            full_name = child.strip()
            # Extract prefix in brackets and remove it from name
            match = re.match(r"^\[(.*?)\]\s*(.*)$", full_name)
            if match:
                out_dict["name_en"] = match.group(2).strip()
                out_dict["status"] = match.group(1).strip()
            else:
                out_dict["name_en"] = full_name
                out_dict["status"] = "Active"
            break


def scrape_talent(url):
    # Send GET request to the talent's page
    response = requests.get(url)

    # Check if request was successful
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return {}

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    out_dict = OrderedDict()
    scrape_talent_name(soup, out_dict)
    scrape_talent_gen(soup, out_dict)
    scrape_talent_socials(soup, out_dict)
    return out_dict


def main():
    # Create talents directory if it doesn't exist
    os.makedirs("talents", exist_ok=True)

    # # Clear existing content in talents/ directory
    # for filename in os.listdir("talents"):
    #     file_path = os.path.join("talents", filename)
    #     if os.path.isfile(file_path):
    #         os.remove(file_path)

    # First get all talent links
    links = scrape_hololive_talents_links()
    print("Found talent links:")
    for name, link in links[:3]:  # Show first 3
        print(link)

    # Then scrape all links and save to individual JSON files
    for name, link in links:
        social_dict = scrape_talent(link)
        filename = f"talents/{name}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(social_dict, f, indent=2, ensure_ascii=False)
        print(f"Saved {filename}")


# Example usage
if __name__ == "__main__":
    main()
