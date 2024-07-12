import os
import sys
import time
import base64
import logging
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def take_screenshot(html_path: str, css_file: str, output_file: str, driver: webdriver.Chrome) -> None:
    """
    Takes a screenshot of the given HTML file with the specified CSS applied.

    Args:
        html_path (str): Path to the HTML file or URL.
        css_file (str): Path to the CSS file to be applied.
        output_file (str): Path where the screenshot will be saved.
        driver (webdriver.Chrome): The Chrome WebDriver instance.
    """
    try:
        # Open the HTML file or URL
        if html_path.startswith(("http://", "https://")):
            driver.get(html_path)
        else:
            driver.get(f"file://{os.path.abspath(html_path)}")

        # Remove current theme.css
        remove_css_script = """
            var links = document.querySelectorAll("link[rel='stylesheet']");
            links.forEach(link => {
                if (link.href.includes('theme.css')) {
                    link.parentNode.removeChild(link);
                }
            });
        """
        driver.execute_script(remove_css_script)

        with open(css_file, "rb") as f:
            css_content = f.read()

        # Encode CSS content as Base64
        encoded_css = base64.b64encode(css_content).decode("utf-8")

        # Inject CSS into HTML using JavaScript
        apply_css_script = f"""
            var style = document.createElement('style');
            style.innerHTML = atob('{encoded_css}');
            document.head.appendChild(style);
        """
        driver.execute_script(apply_css_script)

        # Wait for a while to ensure CSS is applied
        time.sleep(2)

        # Capture screenshot
        driver.save_screenshot(output_file)
        logging.info(f"Screenshot saved to {output_file}")

    except Exception as e:
        logging.error(f"Failed to take screenshot for {css_file}: {e}")


def write_readme(folder_path: str, themes: List[str]) -> None:
    """
    Writes the README file with previews of included themes.

    Args:
        folder_path (str): Path to the folder containing the themes and README.md.
        themes (List[str]): List of theme names.
    """
    readme_path = os.path.join(folder_path, "README.md")
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()

        readme_head = readme.split("## Previews of included themes")[0]
        readme_head += "## Previews of included themes\n"
        readme_head += "".join([f"\n### {theme}\n\n![{theme}](screenshots/{theme}.png)\n" for theme in themes])

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_head)

        logging.info(f"README.md updated with previews of included themes.")

    except FileNotFoundError:
        logging.error(f"README.md not found in {folder_path}")
    except Exception as e:
        logging.error(f"Failed to write README.md: {e}")


def main(folder_path: str, html_path: str) -> None:
    """
    Main function to take screenshots for each CSS file in the folder and update the README.md.

    Args:
        folder_path (str): Path to the folder containing CSS files.
        html_path (str): Path to the HTML file or URL for rendering.
    """
    if not os.path.exists(folder_path):
        logging.error(f'Error: Folder path "{folder_path}" does not exist.')
        return

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode, no GUI
    chrome_options.add_argument("--window-size=1920,1080")  # Set window size to at least 1920x1080

    # Initialize Chrome WebDriver
    chromedriver_path = "/usr/bin/chromedriver"  # Replace with your actual path
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        themes = []
        # Iterate over all files in the folder
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(".css"):
                theme_name = os.path.splitext(filename)[0]
                themes.append(theme_name)
                css_file = os.path.join(folder_path, filename)
                output_file = os.path.join(folder_path, "screenshots", f"{theme_name}.png")

                # Create screenshots folder if it doesn't exist
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Take screenshot for this CSS file
                take_screenshot(html_path, css_file, output_file, driver)

        # Write the README file with the new previews
        write_readme(folder_path, themes)

    finally:
        driver.quit()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Usage: python script_name.py folder_path html_path")
    else:
        folder_path = sys.argv[1]
        html_path = sys.argv[2]
        main(folder_path, html_path)
