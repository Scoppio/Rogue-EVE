message_handler = None
broadcast_handler = None

def send_message(message, color):
    global message_handler
    message_handler.send_message(message, color)


def broadcast_message(tag, body):
    global broadcast_handler
    broadcast_handler.broadcast_message(tag, body)