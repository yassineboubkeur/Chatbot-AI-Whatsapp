def validate_message(msg):
    # write a LOGIC to validate the message
    return 1


def format_response(products):

    print(products[0].name)
    if not products:
        return "No products available."

    message = "Product Catalog:\n\n"
    for i, product in enumerate(products, 1):
        message += f"Product #{i}: {product.name}\n"
        message += f"Price: ${product.price:.2f}\n"
        message += f"Description: {product.description}\n"
        message += "\n" + "-" * 40 + "\n\n"

    message += f"Total Products: {len(products)}"

    return message

