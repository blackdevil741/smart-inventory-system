"""
ai_assistant_service.py

The AI Inventory Assistant. This is a rule-based (not LLM-backed)
natural-language assistant: it matches incoming questions against a
set of intents using keyword/pattern matching, then answers using
live Firestore data -- so every answer is grounded in real inventory
state, never invented.

Why rule-based instead of calling an external LLM API: it keeps the
whole project on Anthropic/Firebase's free tiers with zero API keys
or billing required, while still fully covering the assistant
behaviors described in the project spec (low stock questions,
category questions, reorder suggestions). It trades open-ended
phrasing flexibility for zero cost and zero external dependencies.

Adding a real LLM backend later (e.g. via the Anthropic API) would be
a drop-in replacement for `answer_question()` -- the intent detection
and data-fetching functions below would still be useful as the
"tools" an LLM-based agent could call.
"""

import re
from firebase_config import db

PRODUCTS_COLLECTION = "products"


def _fetch_products():
    return [{**doc.to_dict(), "id": doc.id} for doc in db.collection(PRODUCTS_COLLECTION).stream()]


def _format_product_list(products, empty_message):
    if not products:
        return empty_message
    lines = [f"- {p['name']} ({p.get('quantity', 0)} left, threshold {p.get('min_quantity_threshold', 5)})" for p in products]
    return "\n".join(lines)


# ---- Intent handlers ----
# Each handler takes the question text and returns an answer string.
# Order matters: more specific patterns are checked before general ones.

def _handle_low_stock(question, products):
    low = [p for p in products if 0 < p.get("quantity", 0) <= p.get("min_quantity_threshold", 5)]
    if not low:
        return "Nothing is currently low on stock — all your products are above their reorder threshold. Nice work staying on top of it!"
    listing = _format_product_list(low, "")
    return f"You have {len(low)} product(s) running low:\n{listing}"


def _handle_out_of_stock(question, products):
    out = [p for p in products if p.get("quantity", 0) <= 0]
    if not out:
        return "Nothing is completely out of stock right now."
    listing = _format_product_list(out, "")
    return f"{len(out)} product(s) are out of stock:\n{listing}"


def _handle_highest_stock_category(question, products):
    if not products:
        return "You don't have any products yet, so there's no category data to compare."

    from collections import defaultdict
    totals = defaultdict(int)
    for p in products:
        cat = p.get("category", "Uncategorized").strip() or "Uncategorized"
        totals[cat] += p.get("quantity", 0)

    if not totals:
        return "No categories found yet."

    top_category, top_qty = max(totals.items(), key=lambda kv: kv[1])
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])

    # Be honest when the "highest" isn't a meaningful comparison --
    # e.g. everything is out of stock, or there's only one category.
    if top_qty <= 0:
        return (
            "None of your categories currently have any stock — everything is at 0 units. "
            "You may want to restock soon."
        )
    if len(totals) == 1:
        return f"You only have one category so far: '{top_category}', with {top_qty} units in stock."

    breakdown = ", ".join(f"{cat} ({qty})" for cat, qty in ranked[:5])
    return f"'{top_category}' has the highest stock, with {top_qty} units total. Full breakdown: {breakdown}."


def _handle_lowest_stock_category(question, products):
    if not products:
        return "You don't have any products yet, so there's no category data to compare."

    from collections import defaultdict
    totals = defaultdict(int)
    for p in products:
        cat = p.get("category", "Uncategorized").strip() or "Uncategorized"
        totals[cat] += p.get("quantity", 0)

    if not totals:
        return "No categories found yet."

    if len(totals) == 1:
        cat, qty = next(iter(totals.items()))
        return f"You only have one category so far: '{cat}', with {qty} units in stock."

    bottom_category, bottom_qty = min(totals.items(), key=lambda kv: kv[1])
    return f"'{bottom_category}' has the lowest stock, with only {bottom_qty} units total."


def _handle_reorder_suggestions(question, products):
    candidates = [p for p in products if p.get("quantity", 0) <= p.get("min_quantity_threshold", 5)]
    if not candidates:
        return "Nothing needs reordering right now — all products are comfortably above their threshold."

    candidates.sort(key=lambda p: p.get("quantity", 0))
    suggestions = []
    for p in candidates[:8]:
        threshold = p.get("min_quantity_threshold", 5)
        suggested_qty = max(threshold * 2 - p.get("quantity", 0), threshold)
        suggestions.append(f"- {p['name']}: currently {p.get('quantity', 0)}, suggest ordering ~{suggested_qty} more")
    return f"Based on current stock levels, I'd suggest reordering:\n" + "\n".join(suggestions)


def _handle_total_products(question, products):
    if not products:
        return "You don't have any products in your inventory yet."
    return f"You currently have {len(products)} product(s) in your inventory."


def _handle_stock_value(question, products):
    total_cost = sum(p.get("quantity", 0) * p.get("cost_price", 0) for p in products)
    total_revenue = sum(p.get("quantity", 0) * p.get("selling_price", 0) for p in products)
    return (
        f"Your current stock is worth ₹{total_cost:,.2f} at cost, "
        f"with a potential selling value of ₹{total_revenue:,.2f} "
        f"(potential profit of ₹{total_revenue - total_cost:,.2f})."
    )


def _handle_category_count(question, products):
    categories = {p.get("category", "").strip() for p in products if p.get("category", "").strip()}
    if not categories:
        return "You don't have any categories set up yet."
    names = ", ".join(sorted(categories))
    return f"You have {len(categories)} categor{'y' if len(categories) == 1 else 'ies'}: {names}."


def _find_mentioned_category(question, products):
    """Check if any known category name is mentioned in the question
    (case-insensitive substring match)."""
    categories = {p.get("category", "").strip() for p in products if p.get("category", "").strip()}
    q_lower = question.lower()
    for cat in categories:
        if cat.lower() in q_lower:
            return cat
    return None


def _handle_category_products(question, products):
    category = _find_mentioned_category(question, products)
    if not category:
        return (
            "Which category did you mean? You can ask things like "
            "\"what's in Grains?\" or \"show me Dairy products\"."
        )
    matching = [p for p in products if p.get("category", "").strip().lower() == category.lower()]
    listing = _format_product_list(matching, f"No products found in '{category}'.")
    return f"Products in '{category}' ({len(matching)}):\n{listing}"


def _find_mentioned_product(question, products):
    """Fuzzy-ish match: check if any product name's words appear in the
    question, or vice versa. Not true fuzzy matching (no external
    dependency needed) -- simple substring checks in both directions,
    which handles most real phrasing like 'how much rice do I have'
    matching a product named 'Rice 5kg'."""
    q_lower = question.lower()
    best_match = None
    best_score = 0

    for p in products:
        name_lower = p.get("name", "").lower()
        if not name_lower:
            continue
        if name_lower in q_lower:
            return p  # exact name mentioned, no need to keep looking
        # Partial match: how many of the product's words appear in the question
        name_words = set(re.findall(r"\w+", name_lower))
        score = sum(1 for w in name_words if len(w) > 2 and w in q_lower)
        if score > best_score:
            best_score = score
            best_match = p

    return best_match if best_score > 0 else None


def _handle_product_lookup(question, products):
    product = _find_mentioned_product(question, products)
    if not product:
        return (
            "I couldn't find a product matching that in your inventory. "
            "Try asking with the exact product name, e.g. \"how much Rice 5kg do I have?\""
        )
    qty = product.get("quantity", 0)
    status = "out of stock" if qty <= 0 else (
        "low stock" if qty <= product.get("min_quantity_threshold", 5) else "in stock"
    )
    return (
        f"{product['name']}: {qty} in stock ({status}), category '{product.get('category', 'Uncategorized')}', "
        f"cost ₹{product.get('cost_price', 0):.2f}, selling ₹{product.get('selling_price', 0):.2f}"
        + (f", vendor {product.get('vendor_name')}" if product.get("vendor_name") else "")
        + "."
    )


def _handle_vendor_lookup(question, products):
    vendors = {p.get("vendor_name", "").strip() for p in products if p.get("vendor_name", "").strip()}
    q_lower = question.lower()

    mentioned_vendor = next((v for v in vendors if v.lower() in q_lower), None)
    if mentioned_vendor:
        matching = [p for p in products if p.get("vendor_name", "").strip().lower() == mentioned_vendor.lower()]
        listing = _format_product_list(matching, "")
        return f"Products from {mentioned_vendor} ({len(matching)}):\n{listing}"

    if not vendors:
        return "You haven't recorded any vendor names on your products yet."
    return f"You have products from {len(vendors)} vendor(s): {', '.join(sorted(vendors))}."


def _handle_greeting(question, products):
    return (
        "Hi! I can answer questions about your inventory — try asking things like "
        "\"what products are low?\", \"which category has the highest stock?\", "
        "\"suggest reorder items\", \"what's in Dairy?\", \"how much rice do I have?\", "
        "or \"what's my stock worth?\""
    )


# Patterns checked in order; first match wins. More specific patterns
# (category/vendor/product name lookups) are checked before generic
# ones so, e.g., "what's in Dairy category" doesn't accidentally match
# the generic "highest stock" pattern.
INTENT_PATTERNS = [
    (re.compile(r"\b(out of stock|no stock|zero stock)\b", re.I), _handle_out_of_stock),
    (re.compile(r"\b(low|running low|reorder soon|need(s)? restock)\b", re.I), _handle_low_stock),
    (re.compile(r"\b(reorder|restock|what should i (order|buy))\b", re.I), _handle_reorder_suggestions),
    (re.compile(r"\b(highest|most|top).*(categor|stock)", re.I), _handle_highest_stock_category),
    (re.compile(r"\b(lowest|least|smallest).*(categor|stock)", re.I), _handle_lowest_stock_category),
    (re.compile(r"\bhow many categor", re.I), _handle_category_count),
    (re.compile(r"\b(what'?s in|show me|list).*(categor)?", re.I), _handle_category_products),
    (re.compile(r"\b(vendor|supplier)s?\b", re.I), _handle_vendor_lookup),
    (re.compile(r"\b(how many products|total products|number of products)\b", re.I), _handle_total_products),
    (re.compile(r"\b(worth|value|profit|revenue)\b", re.I), _handle_stock_value),
    (re.compile(r"\b(hi|hello|hey|help|what can you do)\b", re.I), _handle_greeting),
    (re.compile(r"\b(how much|how many|do i have|stock of|quantity of)\b", re.I), _handle_product_lookup),
]


def answer_question(question):
    """Match the question against known intents and answer from live
    Firestore data. Falls back to trying a direct product-name match,
    then a helpful message if nothing at all matches."""
    if not question or not question.strip():
        return "Ask me something about your inventory — like \"what products are low?\" or \"suggest reorder items\"."

    products = _fetch_products()

    for pattern, handler in INTENT_PATTERNS:
        if pattern.search(question):
            return handler(question, products)

    # Last resort: maybe the question just names a product directly
    # ("Rice 5kg?") without any of the trigger phrases above.
    direct_match = _find_mentioned_product(question, products)
    if direct_match:
        return _handle_product_lookup(question, products)

    # Or it names a vendor directly ("What do I get from Amul?")
    # without the word "vendor"/"supplier".
    vendors = {p.get("vendor_name", "").strip() for p in products if p.get("vendor_name", "").strip()}
    q_lower = question.lower()
    if any(v.lower() in q_lower for v in vendors):
        return _handle_vendor_lookup(question, products)

    return (
        "I'm not sure how to answer that yet. Try asking about low stock, "
        "out-of-stock items, which category has the highest stock, reorder "
        "suggestions, a specific product or category by name, vendors, or "
        "your total stock value."
    )
