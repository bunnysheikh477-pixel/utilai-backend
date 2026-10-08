"""Central tool & category seed data — single source of truth for MVP tools."""

from app.models.enums import ProcessingType, ToolStatus

CATEGORIES = [
    {"_id": "pdf", "slug": "pdf", "name": "PDF Tools", "description": "Merge, split, compress and convert PDF files online.", "icon": "file-text", "sort_order": 1},
    {"_id": "image", "slug": "image", "name": "Image Tools", "description": "Compress, resize, crop and convert images.", "icon": "image", "sort_order": 2},
    {"_id": "developer", "slug": "developer", "name": "Developer Tools", "description": "Format, validate and encode developer data.", "icon": "code", "sort_order": 3},
    {"_id": "text", "slug": "text", "name": "Text Tools", "description": "Count, convert and clean text.", "icon": "type", "sort_order": 4},
    {"_id": "calculators", "slug": "calculators", "name": "Calculators", "description": "Financial and everyday calculators.", "icon": "calculator", "sort_order": 5},
    {"_id": "seo", "slug": "seo", "name": "SEO Tools", "description": "Meta tags, robots.txt and SEO utilities.", "icon": "search", "sort_order": 6},
    {"_id": "converters", "slug": "converters", "name": "Converters", "description": "Unit and data conversions.", "icon": "arrow-left-right", "sort_order": 7},
    {"_id": "color", "slug": "color", "name": "Color Tools", "description": "Color format conversion and picking.", "icon": "palette", "sort_order": 8},
    {"_id": "internet", "slug": "internet", "name": "Internet Tools", "description": "DNS, IP, URL and network utilities for the web.", "icon": "globe", "sort_order": 9},
]


def _tool(slug, name, category, ptype, short, **kw):
    return {
        "_id": slug,
        "slug": slug,
        "name": name,
        "category_id": category,
        "category_slug": category,
        "processing_type": ptype,
        "short_description": short,
        "long_description": kw.get("long", short),
        "how_to_use": kw.get("how_to", []),
        "features": kw.get("features", []),
        "faq": kw.get("faq", []),
        "related_tools": kw.get("related", []),
        "seo_title": kw.get("seo_title", f"{name} — Free Online Tool"),
        "meta_description": kw.get("meta", short),
        "keywords": kw.get("keywords", []),
        "is_free": True,
        "is_premium": kw.get("premium", False),
        "requires_auth": False,
        "ads_enabled": True,
        "seo_enabled": True,
        "status": ToolStatus.PUBLISHED.value,
        "accepted_formats": kw.get("formats", []),
        "limits": kw.get("limits", {}),
        "sort_order": kw.get("sort", 0),
        "is_popular": kw.get("popular", False),
    }


TOOLS = [
    # PDF
    _tool("merge-pdf", "Merge PDF", "pdf", ProcessingType.SERVER.value, "Combine multiple PDF files into one document.", related=["split-pdf", "compress-pdf"], popular=True, formats=["pdf"]),
    _tool("split-pdf", "Split PDF", "pdf", ProcessingType.SERVER.value, "Split a PDF into separate pages or ranges.", related=["merge-pdf", "compress-pdf"], formats=["pdf"]),
    _tool("compress-pdf", "Compress PDF", "pdf", ProcessingType.SERVER.value, "Reduce PDF file size while preserving readability.", related=["merge-pdf", "pdf-to-jpg"], popular=True, formats=["pdf"]),
    _tool("jpg-to-pdf", "JPG to PDF", "pdf", ProcessingType.SERVER.value, "Convert JPG images to a PDF document.", related=["pdf-to-jpg", "merge-pdf"], formats=["jpg", "jpeg", "png"]),
    _tool("pdf-to-jpg", "PDF to JPG", "pdf", ProcessingType.SERVER.value, "Convert PDF pages to JPG images.", related=["jpg-to-pdf", "compress-pdf"], formats=["pdf"]),
    # Image
    _tool("compress-image", "Compress Image", "image", ProcessingType.HYBRID.value, "Compress JPG, PNG and WebP images online.", related=["resize-image", "webp-converter"], popular=True, formats=["jpg", "jpeg", "png", "webp"]),
    _tool("resize-image", "Resize Image", "image", ProcessingType.CLIENT.value, "Resize images to exact dimensions.", related=["compress-image", "crop-image"], formats=["jpg", "jpeg", "png", "webp"]),
    _tool("crop-image", "Crop Image", "image", ProcessingType.CLIENT.value, "Crop images to a selected area.", related=["resize-image", "compress-image"], formats=["jpg", "jpeg", "png", "webp"]),
    _tool("jpg-to-png", "JPG to PNG", "image", ProcessingType.CLIENT.value, "Convert JPG images to PNG format.", related=["png-to-jpg", "webp-converter"], popular=True, formats=["jpg", "jpeg"]),
    _tool("png-to-jpg", "PNG to JPG", "image", ProcessingType.CLIENT.value, "Convert PNG images to JPG format.", related=["jpg-to-png", "compress-image"], formats=["png"]),
    _tool("webp-converter", "WebP Converter", "image", ProcessingType.CLIENT.value, "Convert images to and from WebP format.", related=["jpg-to-png", "compress-image"], formats=["webp", "jpg", "jpeg", "png"]),
    _tool("rotate-image", "Rotate Image", "image", ProcessingType.CLIENT.value, "Rotate images 90°, 180° or 270°.", related=["flip-image", "crop-image"], formats=["jpg", "jpeg", "png", "webp"]),
    _tool("flip-image", "Flip Image", "image", ProcessingType.CLIENT.value, "Flip images horizontally or vertically.", related=["rotate-image", "crop-image"], formats=["jpg", "jpeg", "png", "webp"]),
    
    _tool(
    "background-remover",
    "AI Background Remover",
    "image",
    ProcessingType.SERVER.value,
    "Remove image backgrounds automatically using AI and download a transparent PNG.",
    long="Remove backgrounds from JPG, JPEG, PNG and WebP images using the remove.bg API. The processed image is returned as a transparent PNG.",
    how_to_use=[
        "Upload a JPG, JPEG, PNG or WebP image.",
        "Click the remove background button.",
        "Wait while remove.bg processes the image.",
        "Preview and download the transparent PNG."
    ],
    features=[
        "AI-powered background removal",
        "Transparent PNG output",
        "Supports JPG",
        "Supports JPEG",
        "Supports PNG",
        "Supports WebP",
        "Preserves original image dimensions"
    ],
    faq=[
        {
            "question": "Which image formats are supported?",
            "answer": "JPG, JPEG, PNG and WebP images are supported."
        },
        {
            "question": "What format is the result?",
            "answer": "The result is a PNG image with a transparent background."
        },
        {
            "question": "Does the tool use AI?",
            "answer": "Yes. The tool uses the remove.bg API."
        },
        {
            "question": "Will my original image dimensions be preserved?",
            "answer": "Yes. The generated PNG keeps the original image dimensions."
        }
    ],
    related=[
        "compress-image",
        "resize-image",
        "crop-image"
    ],
    seo_title="AI Background Remover — Free Online Background Removal",
    meta="Remove image backgrounds automatically with AI. Upload JPG, PNG or WebP images and download transparent PNG results.",
    keywords=[
        "background remover",
        "ai background remover",
        "remove background",
        "image background remover",
        "transparent background",
        "background removal",
        "birefnet",
        "remove image background"
    ],
    formats=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ],
    popular=True,
    sort=1
),
    
    
    # Developer
    _tool("json-formatter", "JSON Formatter", "developer", ProcessingType.CLIENT.value, "Format and beautify JSON data.", related=["json-validator", "json-minifier"], popular=True),
    _tool("json-validator", "JSON Validator", "developer", ProcessingType.CLIENT.value, "Validate JSON syntax and structure.", related=["json-formatter", "json-minifier"]),
    _tool("json-minifier", "JSON Minifier", "developer", ProcessingType.CLIENT.value, "Minify JSON by removing whitespace.", related=["json-formatter", "json-validator"]),
    _tool("base64-encoder", "Base64 Encoder", "developer", ProcessingType.CLIENT.value, "Encode text to Base64.", related=["base64-decoder", "url-encoder"], popular=True),
    _tool("base64-decoder", "Base64 Decoder", "developer", ProcessingType.CLIENT.value, "Decode Base64 strings to text.", related=["base64-encoder", "url-decoder"]),
    _tool("url-encoder", "URL Encoder", "developer", ProcessingType.CLIENT.value, "Encode URLs and special characters.", related=["url-decoder", "base64-encoder"]),
    _tool("url-decoder", "URL Decoder", "developer", ProcessingType.CLIENT.value, "Decode URL-encoded strings.", related=["url-encoder", "base64-decoder"]),
    _tool("uuid-generator", "UUID Generator", "developer", ProcessingType.CLIENT.value, "Generate random UUID v4 identifiers.", related=["password-generator", "hash-generator"], popular=True),
    _tool("hash-generator", "Hash Generator", "developer", ProcessingType.CLIENT.value, "Generate SHA-256 hashes from text.", related=["base64-encoder", "uuid-generator"]),
    _tool("timestamp-converter", "Timestamp Converter", "developer", ProcessingType.CLIENT.value, "Convert Unix timestamps to readable dates.", related=["uuid-generator", "json-formatter"]),
    _tool("csv-to-json", "CSV to JSON", "developer", ProcessingType.CLIENT.value, "Convert CSV data to JSON format.", related=["json-to-csv", "json-formatter"]),
    _tool("json-to-csv", "JSON to CSV", "developer", ProcessingType.CLIENT.value, "Convert JSON arrays to CSV format.", related=["csv-to-json", "json-formatter"]),
    # Text
    _tool("word-counter", "Word Counter", "text", ProcessingType.CLIENT.value, "Count words, characters and sentences.", related=["character-counter", "case-converter"], popular=True),
    _tool("character-counter", "Character Counter", "text", ProcessingType.CLIENT.value, "Count characters with and without spaces.", related=["word-counter", "case-converter"]),
    _tool("case-converter", "Case Converter", "text", ProcessingType.CLIENT.value, "Convert text between upper, lower and title case.", related=["word-counter", "text-cleaner"]),
    _tool("duplicate-line-remover", "Duplicate Line Remover", "text", ProcessingType.CLIENT.value, "Remove duplicate lines from text.", related=["text-sorter", "text-cleaner"]),
    _tool("text-sorter", "Text Sorter", "text", ProcessingType.CLIENT.value, "Sort lines alphabetically ascending or descending.", related=["duplicate-line-remover", "text-reverser"]),
    _tool("text-reverser", "Text Reverser", "text", ProcessingType.CLIENT.value, "Reverse text character by character.", related=["case-converter", "text-sorter"]),
    _tool("text-cleaner", "Text Cleaner", "text", ProcessingType.CLIENT.value, "Remove extra spaces and clean up text.", related=["duplicate-line-remover", "word-counter"]),
    _tool("lorem-ipsum-generator", "Lorem Ipsum Generator", "text", ProcessingType.CLIENT.value, "Generate placeholder Lorem Ipsum text.", related=["word-counter", "slug-generator"]),
    _tool("slug-generator", "Slug Generator", "text", ProcessingType.CLIENT.value, "Generate URL-friendly slugs from text.", related=["case-converter", "lorem-ipsum-generator"]),
    _tool("password-generator", "Password Generator", "text", ProcessingType.CLIENT.value, "Generate secure random passwords.", related=["uuid-generator", "hash-generator"], popular=True),
    # Calculators
    _tool("percentage-calculator", "Percentage Calculator", "calculators", ProcessingType.CLIENT.value, "Calculate percentages, increases and decreases.", related=["discount-calculator", "emi-calculator"], popular=True),
    _tool("age-calculator", "Age Calculator", "calculators", ProcessingType.CLIENT.value, "Calculate exact age from birth date.", related=["bmi-calculator", "date-calculator"]),
    _tool("bmi-calculator", "BMI Calculator", "calculators", ProcessingType.CLIENT.value, "Calculate Body Mass Index from height and weight.", related=["age-calculator", "percentage-calculator"]),
    _tool("emi-calculator", "EMI Calculator", "calculators", ProcessingType.CLIENT.value, "Calculate monthly EMI for loans.", related=["loan-calculator", "percentage-calculator"], popular=True),
    _tool("discount-calculator", "Discount Calculator", "calculators", ProcessingType.CLIENT.value, "Calculate discounted prices and savings.", related=["percentage-calculator", "gst-calculator"]),
    _tool("gst-calculator", "GST Calculator", "calculators", ProcessingType.CLIENT.value, "Add or remove GST from amounts.", related=["discount-calculator", "percentage-calculator"]),
    _tool("loan-calculator", "Loan Calculator", "calculators", ProcessingType.CLIENT.value, "Calculate total loan interest and payments.", related=["emi-calculator", "percentage-calculator"]),
    # SEO
    _tool("meta-tag-generator", "Meta Tag Generator", "seo", ProcessingType.CLIENT.value, "Generate HTML meta tags for SEO.", related=["open-graph-generator", "serp-preview"], popular=True),
    _tool("robots-txt-generator", "Robots.txt Generator", "seo", ProcessingType.CLIENT.value, "Create a robots.txt file for your website.", related=["sitemap-generator", "meta-tag-generator"]),
    _tool("sitemap-generator", "Sitemap Generator", "seo", ProcessingType.CLIENT.value, "Generate XML sitemap from URL list.", related=["robots-txt-generator", "meta-tag-generator"]),
    _tool("open-graph-generator", "Open Graph Generator", "seo", ProcessingType.CLIENT.value, "Generate Open Graph meta tags for social sharing.", related=["meta-tag-generator", "serp-preview"]),
    _tool("serp-preview", "SERP Preview", "seo", ProcessingType.CLIENT.value, "Preview how your page appears in Google search.", related=["meta-tag-generator", "open-graph-generator"]),
    _tool("utm-builder", "UTM Builder", "seo", ProcessingType.CLIENT.value, "Build UTM tracking URLs for campaigns.", related=["url-encoder", "meta-tag-generator"]),
    _tool("keyword-density-checker", "Keyword Density Checker", "seo", ProcessingType.CLIENT.value, "Analyze keyword frequency in text.", related=["word-counter", "meta-tag-generator"]),
    # Converters
    _tool("unit-converter", "Unit Converter", "converters", ProcessingType.CLIENT.value, "Convert length, weight, temperature and more.", related=["currency-converter", "data-converter"], popular=True),
    _tool("currency-converter", "Currency Converter", "converters", ProcessingType.CLIENT.value, "Convert between major currencies.", related=["unit-converter", "percentage-calculator"]),
    _tool("data-converter", "Data Size Converter", "converters", ProcessingType.CLIENT.value, "Convert bytes, KB, MB, GB and TB.", related=["unit-converter", "percentage-calculator"]),
    # Color
    _tool("hex-to-rgb", "HEX to RGB", "color", ProcessingType.CLIENT.value, "Convert HEX color codes to RGB values.", related=["rgb-to-hex", "color-picker"]),
    _tool("rgb-to-hex", "RGB to HEX", "color", ProcessingType.CLIENT.value, "Convert RGB values to HEX color codes.", related=["hex-to-rgb", "color-picker"]),
    _tool("color-picker", "Color Picker", "color", ProcessingType.CLIENT.value, "Pick colors and get HEX, RGB and HSL values.", related=["hex-to-rgb", "rgb-to-hex"]),
    # Internet
    _tool("url-parser", "URL Parser", "internet", ProcessingType.CLIENT.value, "Break down any URL into protocol, host, path and query parameters.", related=["dns-lookup", "email-validator"], popular=True),
    _tool("dns-lookup", "DNS Lookup", "internet", ProcessingType.CLIENT.value, "Look up DNS records for any domain name.", related=["url-parser", "what-is-my-ip"], popular=True),
    _tool("what-is-my-ip", "What Is My IP", "internet", ProcessingType.CLIENT.value, "Find your public IP address instantly.", related=["dns-lookup", "internet-speed-test"], popular=True),
    _tool("internet-speed-test", "Internet Speed Test", "internet", ProcessingType.CLIENT.value, "Measure your ping, download and upload speeds.", related=["what-is-my-ip", "dns-lookup"], popular=True, sort=1),
    _tool("ip-validator", "IP Address Validator", "internet", ProcessingType.CLIENT.value, "Validate IPv4 and IPv6 addresses.", related=["cidr-calculator", "what-is-my-ip"]),
    _tool("cidr-calculator", "CIDR Calculator", "internet", ProcessingType.CLIENT.value, "Calculate network range, broadcast and host count from CIDR notation.", related=["ip-validator", "mac-address-formatter"]),
    _tool("email-validator", "Email Validator", "internet", ProcessingType.CLIENT.value, "Validate email address format and extract parts.", related=["url-parser", "dns-lookup"]),
    _tool("jwt-decoder", "JWT Decoder", "internet", ProcessingType.CLIENT.value, "Decode JSON Web Token headers and payloads.", related=["base64-decoder", "hash-generator"], popular=True),
    _tool("http-status-lookup", "HTTP Status Lookup", "internet", ProcessingType.CLIENT.value, "Look up HTTP status codes and their meanings.", related=["url-parser", "user-agent-parser"]),
    _tool("user-agent-parser", "User-Agent Parser", "internet", ProcessingType.CLIENT.value, "Parse browser, OS and device from a User-Agent string.", related=["http-status-lookup", "url-parser"]),
    _tool("mac-address-formatter", "MAC Address Formatter", "internet", ProcessingType.CLIENT.value, "Format MAC addresses with colons, dashes or dots.", related=["cidr-calculator", "ip-validator"]),
]

PLANS = [
    {"_id": "plan_free", "name": "Free", "slug": "free", "price_monthly": 0, "price_annual": 0, "features": ["All basic tools", "Standard limits", "Ads supported"], "limits": {"daily_ops": 10, "max_upload_mb": 10}, "is_public": True, "sort_order": 1},
    {"_id": "plan_pro", "name": "Pro", "slug": "pro", "price_monthly": 9, "price_annual": 86, "stripe_price_monthly": "", "stripe_price_annual": "", "features": ["Ad-free", "Higher limits", "Batch processing", "History"], "limits": {"daily_ops": 1000, "max_upload_mb": 50}, "is_public": True, "sort_order": 2},
    {"_id": "plan_business", "name": "Business", "slug": "business", "price_monthly": 29, "price_annual": 278, "stripe_price_monthly": "", "stripe_price_annual": "", "features": ["Everything in Pro", "API access", "Priority processing"], "limits": {"daily_ops": 10000, "max_upload_mb": 100}, "is_public": True, "sort_order": 3},
]
