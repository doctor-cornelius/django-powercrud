class TableMixin:
    """
    Provides methods for table styling and layout.
    """
    def get_table_pixel_height_other_page_elements(self) -> str:
        """ Returns the height of other elements on the page that the table is
        displayed on. After subtracting this (in pixels) from the page height,
        the table height will be calculated (in a css style in list.html) as
        {{ get_table_max_height }}% of the remaining viewport height.
        """
        return f"{self.table_pixel_height_other_page_elements or 0}px" #px

    def get_table_max_height(self) -> int:
        """Returns the proportion of visible space on the viewport after subtracting
        the height of other elements on the page that the table is displayed on,
        as represented by get_table_pixel_height_other_page_elements().

        The table height is calculated in a css style for max-table-height in list.html.
        """
        return self.table_max_height

    def get_table_max_col_width(self):
        # The max width for the table columns in object_list.html - in characters
        return f"{self.table_max_col_width}ch" or '25ch'

    def get_table_header_min_wrap_width(self):
        # The max width for the table columns in object_list.html - in characters
        if self.table_header_min_wrap_width is None:
            return self.get_table_max_col_width()
        elif int(self.table_header_min_wrap_width) > int(self.table_max_col_width):
            return self.get_table_max_col_width()
        else:
            return f"{self.table_header_min_wrap_width}ch" #ch

    def get_table_classes(self):
        """
        Get the table classes.
        """
        return self.table_classes

    def get_action_button_classes(self):
        """
        Get the action button classes.
        """
        return self.action_button_classes

    def get_extra_button_classes(self):
        """
        Get the extra button classes.
        """
        return self.extra_button_classes