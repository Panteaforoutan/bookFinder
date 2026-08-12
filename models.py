class Book:
    def __init__(self, title, author, categories=None, description=None, boundary_box=None):
        self.title = title
        self.author = author
        self.categories = categories
        self.description = description
        self.boundary_box = boundary_box