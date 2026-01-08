echo "Installing required fonts..."

FONT_URL="https://github.com/zed-industries/zed-fonts/releases/download/1.2.0/zed-sans-1.2.0.zip"
FONT_DIR="$HOME/.fonts/zed-sans"
TEMP_ZIP="/tmp/zed-sans-1.2.0.zip"

# Check if fonts are already installed
if [ ! -d "$FONT_DIR" ]; then
    echo "Downloading fonts from $FONT_URL..."
    curl -L -o "$TEMP_ZIP" "$FONT_URL"

    echo "Extracting fonts to $FONT_DIR..."
    mkdir -p "$FONT_DIR"
    unzip -o "$TEMP_ZIP" -d "$FONT_DIR"

    echo "Cleaning up..."
    rm "$TEMP_ZIP"
else
    echo "Fonts are already installed. Skipping download and extraction."
fi

# Copy local fonts if not already present
if [ ! -d "$HOME/.fonts/tabler-icons" ]; then
    echo "Copying local fonts to $HOME/.fonts/tabler-icons..."
    mkdir -p "$HOME/.fonts/tabler-icons"
    cp -r "$INSTALL_DIR/assets/fonts/"* "$HOME/.fonts/tabler-icons"
else
    echo "Local fonts are already installed. Skipping copy."
fi


