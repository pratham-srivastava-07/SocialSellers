from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Set up your API keys
GENAI_API_KEY = "AIzaSyAH4nMhPaJyV0U4WCIPd5JPR0m5vd6RPz0"  # Replace with your actual Gemini API key
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAABU4wwEAAAAAfQ6aNhf8Ity2iJAhLyoO7x1AIx0%3DHmOHVyi7XOByv1sgOESFo3bDNzCewy7whjVvb83WDjxN9bFVrw"  # Replace with your Twitter Bearer Token
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
X_IG_APP_ID = "936619743392459"  # Updated Instagram App ID

genai.configure(api_key=GENAI_API_KEY)

def generate_content_with_gemini(prompt):
    try:
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return response.text.strip() if response else ""
    except Exception as e:
        print(f"Gemini error: {e}")
        return ""

def parse_product_details(text):
    product_details = {
        "title": "",
        "price": "",
        "category": "General",
        "brand": "Unknown",
        "attributes": [],
    }

    match_title = re.search(
        r"([A-Za-z0-9\s\-]+)\s+(is now available|now available|for sale|on sale|buy now)",
        text, re.IGNORECASE)
    if match_title:
        product_details["title"] = match_title.group(1).strip()

    match_price = re.search(
        r"(Rs\.\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)|(USD\s?\d+(\.\d{2})?)",
        text, re.IGNORECASE)
    if match_price:
        product_details["price"] = match_price.group(0).strip()

    match_attributes = re.findall(
        r"(Black|Grey|Blue|Red|Green|Yellow|Gold|Silver|Cotton|Silk|Polyester|Leather|Wool)",
        text, re.IGNORECASE)
    if match_attributes:
        product_details["attributes"] = list(set(attr.capitalize() for attr in match_attributes))

    return product_details

def generate_product_listing(content):
    details = parse_product_details(content)

    # Prompts for additional data generation
    dimensions_prompt = f"Generate typical dimensions (height, width, length) for a product category like {details['category']}."
    weight_prompt = f"Estimate the typical weight of a product in the category {details['category']}."
    type_prompt = f"What is the product type for a category like {details['category']}?"
    benefits_prompt = f"What are the key benefits of a product in the {details['category']} category?"
    audience_prompt = f"Who is the target audience for a product in the {details['category']} category?"

    # Fetch data using Gemini API
    dimensions = generate_content_with_gemini(dimensions_prompt) or "0 cm x 0 cm x 0 cm"
    weight = generate_content_with_gemini(weight_prompt) or "0 kg"
    product_type = generate_content_with_gemini(type_prompt) or details["category"]
    product_benefits = generate_content_with_gemini(benefits_prompt) or "Not specified"
    target_audience = generate_content_with_gemini(audience_prompt) or "General audience"

    # Parse dimensions
    dims_match = re.match(r"(\d+)\s?cm\s*x\s*(\d+)\s?cm\s*x\s*(\d+)\s?cm", dimensions)
    height, width, length = dims_match.groups() if dims_match else ("0", "0", "0")

    # Parse weight
    weight_value = re.match(r"(\d+(\.\d{1,2})?)\s?kg", weight)
    weight_kg = weight_value.group(1) if weight_value else "0"

    # Structure description with all variables
    product_title = details["title"]
    product_price = details["price"]
    product_attributes = details["attributes"]
    product_materials = ", ".join(details["attributes"]) if details["attributes"] else "Not specified"
    product_colors = ", ".join(attr for attr in details["attributes"] if attr.lower() in ["black", "grey", "blue", "red", "green", "yellow", "gold", "silver"]) or "Not specified"
    warranty_info = "Warranty not provided"  # Placeholder for warranty

    # Optimized description
    detailed_description = (
        f"{product_title} is an excellent {product_type} available at {product_price}. "
        f"It features high-quality materials such as {product_materials} and comes in {product_colors}. "
        f"It is designed for {target_audience}, offering benefits like {product_benefits}. "
        f"Dimensions: {height} cm x {width} cm x {length} cm. Weight: {weight_kg} kg."
    )

    # Create structured JSON output
    return {
        "metadata": {
            "asin": "DefaultASIN",
            "availability": "In Stock",
            "category": product_type,
            "brand": details["brand"],
        },
        "product_details": {
            "title": product_title,
            "price": product_price,
            "attributes": product_attributes,
            "materials": product_materials,
            "colors": product_colors,
            "target_audience": target_audience,
            "benefits": product_benefits,
            "description": detailed_description,
        },
        "dimensions": {
            "height": height,
            "width": width,
            "length": length,
            "unit": "cm",
        },
        "item_weight": {
            "value": weight_kg,
            "unit": "kg",
        },
        "additional_info": {
            "warranty": warranty_info,
        }
    }
@app.route('/twitter-data', methods=['POST'])
def twitter_scraper():
    try:
        tweet_url = request.json.get("tweet_url")
        if not tweet_url:
            return jsonify({"error": "Tweet URL is required"}), 400

        tweet_id = re.search(r"status/(\d+)", tweet_url)
        if not tweet_id:
            return jsonify({"error": "Invalid Tweet URL format"}), 400

        tweet_api_url = f"https://api.twitter.com/2/tweets/{tweet_id.group(1)}?tweet.fields=text"
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        response = requests.get(tweet_api_url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": f"Failed to fetch Twitter data: {response.status_code}"}), response.status_code

        tweet_content = response.json().get("data", {}).get("text", "")
        listing = generate_product_listing(tweet_content)
        return jsonify(listing)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/instagram-data', methods=['POST'])
def instagram_scraper():
    try:
        url = request.json.get("url")
        if not url:
            return jsonify({"error": "Instagram URL is required"}), 400

        shortcode = re.search(r"instagram\.com/(?:p|reel)/([A-Za-z0-9-_]+)", url)
        if not shortcode:
            return jsonify({"error": "Invalid Instagram URL format"}), 400

        # Use session for cookies and headers
        session = requests.Session()
        session.cookies.set("sessionid", "your_valid_sessionid_here")

        # Updated GraphQL URL
        graphql_url = f"https://www.instagram.com/p/{shortcode.group(1)}/?__a=1&__d=dis"
        headers = {
            "User-Agent": USER_AGENT,
            "X-IG-App-ID": X_IG_APP_ID,
        }

        response = session.get(graphql_url, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to fetch Instagram data: {response.status_code}"}), response.status_code

        # Log raw response for debugging
        json_data = response.json()
        print(f"Raw Instagram response: {json_data}")

        # Parse caption from response
        caption = json_data.get('graphql', {}).get('shortcode_media', {}).get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', "")
        if not caption:
            return jsonify({"error": "Could not extract caption from the Instagram post."}), 400

        # Generate product listing from Instagram caption
        listing = generate_product_listing(caption)
        return jsonify(listing)

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8000)