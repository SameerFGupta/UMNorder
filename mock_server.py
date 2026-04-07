from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

html_content = """
<!DOCTYPE html>
<html>
<head><title>Mock Tapin2</title></head>
<body>
    <button id="go-to-all-locations-button">All Locations</button>
    <ul>
        <li id="location-1">Mock Location</li>
    </ul>
    <ul>
        <li class="item" data-title="burger">Burger</li>
    </ul>
    <div id="product-modal" style="display: none;">
        <button class="qc btn-primary">Add</button>
        <button data-dismiss="modal">Close</button>
    </div>
    <a id="cart" href="#">Cart</a>
    <a id="continue-link" href="#">Continue</a>
    <input id="name" />
    <input id="phone" />
    <button id="continue-button">Submit</button>
    <div id="content-status"></div>

    <script>
        document.getElementById("go-to-all-locations-button").onclick = function() {
            // Do nothing
        };
        document.querySelectorAll(".item").forEach(item => {
            item.onclick = function() {
                setTimeout(() => {
                    document.getElementById("product-modal").style.display = "block";
                }, 100); // 100ms delay to open modal
            };
        });
        document.querySelector(".qc.btn-primary").onclick = function() {
            document.getElementById("product-modal").style.display = "none";
        };
        document.getElementById("continue-button").onclick = function() {
            setTimeout(() => {
                document.getElementById("content-status").innerText = "Thank you for your order";
                // Replace body to simulate new page
                document.body.innerHTML = "Thank you confirmed";
            }, 100);
        };
    </script>
</body>
</html>
"""

@app.get("/{path:path}")
async def get_page(path: str):
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
