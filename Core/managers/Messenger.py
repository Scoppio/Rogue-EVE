message_handler = None


def send_message(message, color):
    global message_handler
    message_handler.send_message(message, color)
