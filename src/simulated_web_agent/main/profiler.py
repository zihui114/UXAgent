import tiktoken

class TokenProfiler:
    """
    Counts the number of tokens of individual chats. Uses gpt-5-mini by default.
    """
    def __init__(self, model: str = "gpt-5-mini"):
        self.encoding = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str):
        """
        Counts the number of tokens in a given string determined by the model. Uses gpt-5-mini by default
        """
        return len(self.encoding.encode(text))
