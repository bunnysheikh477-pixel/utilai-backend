from app.birefnet import birefnet_service
from typing import Any, Callable
from app.tools.internet import internet_tools
from app.tools.pdf import operations as pdf_ops
from app.tools.ai import ai_tool as ai_ops
from app.tools.internet import email_tools as email_ops    

# Registry mapping tool slug -> processor function
PROCESSORS: dict[str, Callable[..., Any]] = {

    # =========================
    # PDF TOOLS
    # =========================
    "merge-pdf": pdf_ops.merge_pdfs,
    "split-pdf": pdf_ops.split_pdf,
    "compress-pdf": pdf_ops.compress_pdf,
    "pdf-to-jpg": pdf_ops.pdf_to_jpg,
    "images-to-pdf": pdf_ops.images_to_pdf,
    "pdf-info": pdf_ops.pdf_info,
    "rotate-pdf-page": pdf_ops.rotate_pdf_page,
    "delete-pdf-page": pdf_ops.delete_pdf_page,
    "add-text-to-pdf": pdf_ops.add_text_to_pdf,
    "add-rectangle-to-pdf": pdf_ops.add_rectangle_to_pdf,
    "add-line-to-pdf": pdf_ops.add_line_to_pdf,
    "add-image-to-pdf": pdf_ops.add_image_to_pdf,
    "add-watermark": pdf_ops.add_watermark,
    "extract-pdf-pages": pdf_ops.extract_pdf_pages,
    "jpg-to-pdf": pdf_ops.jpg_to_pdf,
    "pdf-editor": pdf_ops.edit_pdf,

    # =========================
    # IMAGE TOOLS
    # =========================
    "compress-image": pdf_ops.compress_image,
    "background-remover": birefnet_service.remove_background,

    # =========================
    # AI / TEXT TOOLS
    # =========================
    "text-summarizer": ai_ops.text_summarizer,
    "text-analyzer": ai_ops.text_analyzer,
    "keyword-extractor": ai_ops.sentiment_keyword_analyzer,
    "sentiment-analyzer": ai_ops.sentiment_keyword_analyzer,
    "password-generator": ai_ops.password_generator,
    "email-validator": ai_ops.email_validator,
    "text-case-converter": ai_ops.text_case_converter,
    "human-summarizer": ai_ops.human_summarizer,
    "ai-likelihood-detector": ai_ops.human_summarizer,
    "humanize-text": ai_ops.human_summarizer,
    "text-cleaner": ai_ops.text_cleaner,
    "slug-generator": ai_ops.slug_generator,
    "random-text-generator": ai_ops.random_text_generator,
    # "summarize-humanized-text": ai_ops.human_summarizer,




    # =========================
    # INTERNET TOOLS
    # =========================
    "url-encoder": internet_tools.url_encoder,
    "url-decoder": internet_tools.url_decoder,
    "url-validator": internet_tools.url_validator,
    "url-parser": internet_tools.url_parser,
    "query-parser": internet_tools.query_parser,
    "query-builder": internet_tools.query_builder,

    "redirect-checker": internet_tools.redirect_checker,
    "http-status-checker": internet_tools.http_status_checker,
    "http-header-checker": internet_tools.http_header_checker,
    "website-response-time": internet_tools.website_response_time,
    "website-metadata": internet_tools.website_metadata,
    "website-text-extractor": internet_tools.website_text_extractor,

    "dns-lookup": internet_tools.dns_lookup,
    "a-record-lookup": internet_tools.a_record_lookup,
    "aaaa-record-lookup": internet_tools.aaaa_record_lookup,
    "mx-record-lookup": internet_tools.mx_record_lookup,
    "txt-record-lookup": internet_tools.txt_record_lookup,
    "ns-record-lookup": internet_tools.ns_record_lookup,
    "cname-record-lookup": internet_tools.cname_record_lookup,
    "ip-lookup": internet_tools.ip_lookup,
    "domain-to-ip": internet_tools.domain_to_ip,
    "reverse-dns-lookup": internet_tools.reverse_dns_lookup,
    "ping-check": internet_tools.ping_check,
    "ssl-checker": internet_tools.ssl_checker,
    "robots-txt-checker": internet_tools.robots_txt_checker,
    "sitemap-checker": internet_tools.sitemap_checker,
    "link-extractor": internet_tools.link_extractor,
    "email-extractor": internet_tools.email_extractor,
    "website-word-counter": internet_tools.website_word_counter,
    "user-agent-parser": internet_tools.user_agent_parser,



    # =========================
    # EMAIL TOOLS
    # =========================
    "generate-random-email": email_ops.generate_random_email,
    "generate-otp": email_ops.generate_otp,
    "verify-otp": email_ops.verify_otp,
}

def get_processor(slug: str):
    return PROCESSORS.get(slug)