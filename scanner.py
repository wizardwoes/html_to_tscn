from tag_token import Token, TagCategory
from bs4 import NavigableString


class HtmlScanner:
    def __init__(self, source) -> None:
        self.source = source
        self.tokens = []
        self.current_tag = source
        self.scope = []

    def _is_at_end(self) -> bool:
        if self.current_tag.next_element:
            return False
        return True

    def peek(self):
        if self._is_at_end():
            return None
        return self.current_tag

    def peek_next(self):
        if self._is_at_end():
            return None
        return self.current_tag.next_element

    def _advance(self):
        self.current_tag = self.current_tag.next_element

    def add_token(self, token: Token) -> None:
        self.tokens.append(token)

    def scan_tokens(self) -> list[Token]:
        while not self._is_at_end():
            self.scan_token()

        self.add_token(Token(TagCategory.EOF))

        return self.tokens

    def clean_string(self, text):
        fmt = [ts.strip() for ts in text.split("\n")]
        cleaned = " ".join(fmt).strip()
        return cleaned

    def scan_token(self):
        self._advance()

        match self.current_tag:
            case NavigableString() as tag:
                if tag != "\n":
                    cleaned = self.clean_string(tag.string)
                    self.add_token(Token(TagCategory.TEXT, cleaned))

            case _ as tag:
                match tag.name:
                    case "h1":
                        next_str = self.clean_string(self.peek().string)
                        self.add_token(
                            Token(
                                TagCategory.H1,
                                str_val=next_str,
                                attrs=tag.attrs,
                            )
                        )
                        self._advance()
                    case "h4":
                        next_str = self.clean_string(self.peek().string)
                        self.add_token(
                            Token(
                                TagCategory.H4,
                                str_val=next_str,
                                attrs=tag.attrs,
                            )
                        )
                        self._advance()
                    case "p":
                        self.add_token(Token(TagCategory.P, attrs=tag.attrs))
                    case "title":
                        self.add_token(Token(TagCategory.TITLE, attrs=tag.attrs))
                    case "a":
                        self.add_token(Token(TagCategory.A, attrs=tag.attrs))
                    case "em":
                        next_str = self.clean_string(self.peek().string)
                        self.add_token(
                            Token(
                                TagCategory.EM,
                                str_val=next_str,
                                attrs=tag.attrs,
                            )
                        )
                        self._advance()
                    case "i":
                        self.add_token(Token(TagCategory.I, attrs=tag.attrs))
                    case "hr":
                        self.add_token(Token(TagCategory.HR, attrs=tag.attrs))
                    case "meta":
                        self.add_token(Token(TagCategory.METADATA, attrs=tag.attrs))
                    case "div":
                        self.add_token(Token(TagCategory.DIV, attrs=tag.attrs))
                    case "span":
                        next_str = self.clean_string(self.peek().string)
                        self.add_token(
                            Token(
                                TagCategory.SPAN,
                                str_val=next_str,
                                attrs=tag.attrs,
                            )
                        )
                        self._advance()
                    case "body":
                        self.add_token(Token(TagCategory.BODY, attrs=tag.attrs))
                    case "footer":
                        self.add_token(Token(TagCategory.FOOTER, attrs=tag.attrs))
                    case "head":
                        self.add_token(Token(TagCategory.HEAD, attrs=tag.attrs))
                    case "img":
                        self.add_token(Token(TagCategory.IMG, attrs=tag.attrs))
                    case "nav":
                        self.add_token(Token(TagCategory.NAV, attrs=tag.attrs))
                    case "ul":
                        self.add_token(Token(TagCategory.UL, attrs=tag.attrs))
                    case "li":
                        self.add_token(Token(TagCategory.LI, attrs=tag.attrs))
                    case "blockquote":
                        self.add_token(Token(TagCategory.BLOCKQUOTE, attrs=tag.attrs))
                    case _:
                        self.add_token(Token(TagCategory.FLOW, attrs=tag.attrs))

        try:
            if list(self.peek().children):
                self.add_token(Token(TagCategory.START_CHILDREN, self.peek().name))
                self.scope.append(self.peek())
        except AttributeError:
            pass

        try:
            while self.peek_next() not in self.scope[-1].children:
                self.add_token(Token(TagCategory.END_CHILDREN, self.scope[-1].name))
                self.scope.pop()
        except IndexError:
            pass
