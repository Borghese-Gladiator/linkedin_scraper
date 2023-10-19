import traceback

class ElementCountMismatchException(Exception):
    def __init__(self, failed_code_location, expected_count, actual_count):
        self.failed_code_location = failed_code_location
        self.expected_count = expected_count
        self.actual_count = actual_count
        self.line_number = traceback.extract_stack()[-2][1]  # Get the line number of the caller
        super().__init(f"{failed_code_location}: Expected {expected_count} elements, but found {actual_count} elements on line {self.line_number}.")
