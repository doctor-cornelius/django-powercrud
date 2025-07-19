#!/bin/bash

# run the code as follows (it will use the current system date in format YYYYMMDD)
# ./newblog.sh SHORTNAME category1,category2,category3

DATE=$(date +%Y%m%d)
SHORTNAME=$1
CATEGORIES=$2

# provide help if 1st parm is ? or --help or -h
if [[ -z $SHORTNAME || $SHORTNAME == "?" || $SHORTNAME == "--help" || $SHORTNAME == "-h" ]]; then
    echo "Usage: ./newblog.sh SHORTNAME category1,category2,category3"
    echo "Where SHORTNAME is the suffix for the filename"
    echo "eg: ./newblog.sh mytrip photography,travel"
    exit 1
fi

# Create the filename
FILENAME="./docs/mkdocs/blog/posts/${DATE}_${SHORTNAME}.md"

# Check if file already exists
if [[ -e $FILENAME ]]; then
  echo "File '$FILENAME' already exists."
  echo "Please choose a different SHORTNAME or remove the existing file."
  exit 1
fi

# Create the file
mkdir -p "$(dirname "$FILENAME")"
touch "$FILENAME"

# Add header to the file
echo "---" >> "$FILENAME"
echo "date: $(date +%Y-%m-%d)" >> "$FILENAME"

IFS=',' read -ra CATEGORY_ARRAY <<< "$CATEGORIES"
echo "categories:" >> "$FILENAME"
for category in "${CATEGORY_ARRAY[@]}"; do
  echo "  - $category" >> "$FILENAME"
done

echo "---" >> "$FILENAME"

# Add system date in format # DD-MMM-YYYY
echo "# $(date +"%d-%b-%Y")" >> "$FILENAME"
echo "<!-- more -->" >> "$FILENAME"

echo "File created: $FILENAME"
