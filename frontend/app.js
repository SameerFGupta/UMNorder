const API_BASE = "http://localhost:8000";

function show_tab(tab_name, clicked_button = null) {
  document.querySelectorAll(".tab-content").forEach((tab) => {
    tab.classList.remove("active");
  });

  document.querySelectorAll(".tab-button").forEach((btn) => {
    btn.classList.remove("active");
  });

  document.getElementById(`${tab_name}-tab`).classList.add("active");

  /* We activate the appropriate UI tab button to provide a clear visual indicator of the current active view to the user. */
  if (clicked_button) {
    clicked_button.classList.add("active");
  } else {
    const buttons = document.querySelectorAll(".tab-button");
    buttons.forEach((btn) => {
      const btn_text = btn.textContent.toLowerCase();
      if (
        (tab_name === "presets" && btn_text.includes("presets")) ||
        (tab_name === "create" && btn_text.includes("create")) ||
        (tab_name === "users" && btn_text.includes("users"))
      ) {
        btn.classList.add("active");
      }
    });
  }

  /* We dynamically load data on tab switch instead of upfront to minimize initial payload and ensure fresh data. */
  if (tab_name === "presets") {
    load_presets();
  } else if (tab_name === "users") {
    load_users();
  }
}

/* We use document.createElement to natively escape HTML and prevent Cross-Site Scripting (XSS) vulnerabilities, as assigning to innerHTML directly with user input is unsafe. */
function escape_html(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function load_presets() {
  const presets_list = document.getElementById("presets-list");
  presets_list.textContent = "";
  const loading_div = document.createElement("div");
  loading_div.className = "loading";
  loading_div.textContent = "Loading presets...";
  presets_list.appendChild(loading_div);

  try {
    const response = await fetch(`${API_BASE}/api/presets`, {
      headers: { "ngrok-skip-browser-warning": "true" },
    });
    if (!response.ok) throw new Error("Failed to load presets");

    const presets = await response.json();

    presets_list.textContent = "";
    if (presets.length === 0) {
      const no_presets_div = document.createElement("div");
      no_presets_div.className = "loading";
      no_presets_div.textContent = "No presets yet. Create one to get started!";
      presets_list.appendChild(no_presets_div);
      return;
    }

    /* We load users upfront to build a map, preventing N+1 network requests when resolving user names for presets. */
    const users_response = await fetch(`${API_BASE}/api/users`, {
      headers: { "ngrok-skip-browser-warning": "true" },
    });
    const users = await users_response.json();
    const user_map = {};
    users.forEach((u) => (user_map[u.id] = u));

    presets.forEach((preset) => {
      const user = user_map[preset.user_id] || {
        name: "Unknown",
        phone_number: "N/A",
      };
      const card = document.createElement("div");
      card.className = "preset-card";

      const h3 = document.createElement("h3");
      h3.textContent = preset.preset_name;
      card.appendChild(h3);

      const items_div = document.createElement("div");
      items_div.className = "items";
      const items_strong = document.createElement("strong");
      items_strong.textContent = "Items:";
      items_div.appendChild(items_strong);

      const ul = document.createElement("ul");
      let items = preset.items;
      if (typeof items === "string") {
        try {
          items = JSON.parse(items);
        } catch (e) {
          items = [];
        }
      }

      if (items && items.length > 0) {
        items.forEach((item) => {
          const li = document.createElement("li");
          if (typeof item === "string") {
            li.textContent = item;
          } else {
            li.textContent = item.name;
            if (item.modifiers && item.modifiers.length > 0) {
              const span = document.createElement("span");
              span.style.color = "#666";
              span.style.fontSize = "0.9em";
              span.textContent = ` (${item.modifiers.join(", ")})`;
              li.appendChild(span);
            }
          }
          ul.appendChild(li);
        });
      }
      items_div.appendChild(ul);
      card.appendChild(items_div);

      const user_div = document.createElement("div");
      user_div.style.marginBottom = "10px";
      user_div.style.fontSize = "0.9rem";
      user_div.style.color = "#666";

      const user_strong = document.createElement("strong");
      user_strong.textContent = "User:";
      user_div.appendChild(user_strong);
      user_div.appendChild(
        document.createTextNode(` ${user.name} (${user.phone_number})`),
      );
      user_div.appendChild(document.createElement("br"));

      const location_strong = document.createElement("strong");
      location_strong.textContent = "Location:";
      user_div.appendChild(location_strong);
      if (preset.location_name) {
        user_div.appendChild(
          document.createTextNode(` ${preset.location_name}`),
        );
      } else {
        const em = document.createElement("em");
        em.textContent = " Any available";
        user_div.appendChild(em);
      }
      card.appendChild(user_div);

      const order_btn = document.createElement("button");
      order_btn.className = "btn btn-order";
      order_btn.textContent = "ORDER NOW";
      order_btn.onclick = (e) =>
        place_order(preset.id, preset.preset_name, e.target);
      card.appendChild(order_btn);

      const delete_btn = document.createElement("button");
      delete_btn.className = "btn btn-delete";
      delete_btn.textContent = "Delete Preset";
      delete_btn.onclick = () => delete_preset(preset.id);
      card.appendChild(delete_btn);

      presets_list.appendChild(card);
    });
  } catch (error) {
    presets_list.textContent = "";
    const error_div = document.createElement("div");
    error_div.className = "loading";
    error_div.style.color = "#ff6b6b";
    error_div.textContent = `Error loading presets: ${error.message}`;
    presets_list.appendChild(error_div);
  }
}

async function load_users() {
  const users_list = document.getElementById("users-list");
  users_list.textContent = "";
  const loading_div = document.createElement("div");
  loading_div.className = "loading";
  loading_div.textContent = "Loading users...";
  users_list.appendChild(loading_div);

  try {
    const response = await fetch(`${API_BASE}/api/users`, {
      headers: { "ngrok-skip-browser-warning": "true" },
    });
    if (!response.ok) throw new Error("Failed to load users");

    const users = await response.json();

    users_list.textContent = "";
    if (users.length === 0) {
      const no_users_div = document.createElement("div");
      no_users_div.className = "loading";
      no_users_div.textContent = "No users yet. Add one to get started!";
      users_list.appendChild(no_users_div);
      return;
    }

    users.forEach((user) => {
      const card = document.createElement("div");
      card.className = "user-card";
      const inner_div = document.createElement("div");

      const strong = document.createElement("strong");
      strong.textContent = user.name;
      inner_div.appendChild(strong);
      inner_div.appendChild(document.createElement("br"));

      const span = document.createElement("span");
      span.style.color = "#666";
      span.textContent = user.phone_number;
      inner_div.appendChild(span);

      card.appendChild(inner_div);
      users_list.appendChild(card);
    });
  } catch (error) {
    users_list.textContent = "";
    const error_div = document.createElement("div");
    error_div.className = "loading";
    error_div.style.color = "#ff6b6b";
    error_div.textContent = `Error loading users: ${error.message}`;
    users_list.appendChild(error_div);
  }
}

async function load_users_for_dropdown() {
  const user_select = document.getElementById("user-select");

  try {
    const response = await fetch(`${API_BASE}/api/users`, {
      headers: { "ngrok-skip-browser-warning": "true" },
    });
    if (!response.ok) throw new Error("Failed to load users");

    const users = await response.json();

    user_select.textContent = "";
    const default_option = document.createElement("option");
    default_option.value = "";
    default_option.textContent = "Select a user...";
    user_select.appendChild(default_option);

    users.forEach((user) => {
      const option = document.createElement("option");
      option.value = user.id;
      option.textContent = `${user.name} (${user.phone_number})`;
      user_select.appendChild(option);
    });
  } catch (error) {
    console.error("Error loading users:", error);
  }
}

document
  .getElementById("create-user-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("user-name").value;
    const phone = document.getElementById("user-phone").value;

    try {
      const response = await fetch(`${API_BASE}/api/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({ name, phone_number: phone }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create user");
      }

      show_status("User created successfully!", "success");
      document.getElementById("create-user-form").reset();
      load_users();
      load_users_for_dropdown();
    } catch (error) {
      show_status(`Error: ${error.message}`, "error");
    }
  });

function add_item_row(item_name = "", modifiers = []) {
  const container = document.getElementById("items-container");
  const item_index = container.children.length;

  const item_div = document.createElement("div");
  item_div.className = "item-row";

  item_div.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
      <strong>Item ${item_index + 1}</strong>
      <button type="button" class="btn btn-sm">Remove</button>
    </div>
    <div class="form-group" style="margin-bottom: 15px;">
      <label>Item Name:</label>
      <input type="text" class="item-name" placeholder="e.g., Hamburger" required>
    </div>
    <div class="form-group" style="margin-bottom: 0;">
      <label>Modifiers (comma-separated):</label>
      <input type="text" class="item-modifiers" placeholder="e.g., Bun, American Cheese">
      <small style="display: block; color: #888; margin-top: 8px; font-size: 0.85rem;">Enter modifier names exactly as they appear</small>
    </div>
  `;

  item_div.querySelector("button").onclick = (e) => remove_item_row(e.target);
  item_div.querySelector(".item-name").value = item_name;
  item_div.querySelector(".item-modifiers").value = modifiers.join(", ");

  container.appendChild(item_div);
}

function remove_item_row(button) {
  button.closest(".item-row").remove();
  /* Re-indexing rows ensures the UI numbering remains contiguous and predictable after row deletions. */
  const container = document.getElementById("items-container");
  Array.from(container.children).forEach((row, index) => {
    row.querySelector("strong").textContent = `Item ${index + 1}`;
  });
}

document
  .getElementById("create-preset-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const user_id = parseInt(document.getElementById("user-select").value);
    const preset_name = document.getElementById("preset-name").value;
    const location_name =
      document.getElementById("location-select").value || null;

    const item_rows = document.querySelectorAll(".item-row");
    const items = [];

    item_rows.forEach((row) => {
      const item_name = row.querySelector(".item-name").value.trim();
      const modifiers_text = row.querySelector(".item-modifiers").value.trim();

      if (item_name) {
        const modifiers = modifiers_text
          ? modifiers_text
              .split(",")
              .map((m) => m.trim())
              .filter((m) => m.length > 0)
          : [];
        items.push({
          name: item_name,
          modifiers: modifiers,
        });
      }
    });

    if (items.length === 0) {
      show_status("Please add at least one item", "error");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/presets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({
          user_id: user_id,
          preset_name: preset_name,
          items: items,
          location_name: location_name,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create preset");
      }

      show_status("Preset created successfully!", "success");
      document.getElementById("create-preset-form").reset();
      document.getElementById("items-container").textContent = "";
      show_tab("presets");
      load_presets();
    } catch (error) {
      show_status(`Error: ${error.message}`, "error");
    }
  });

async function place_order(preset_id, preset_name, button_element = null) {
  const button =
    button_element ||
    (typeof event !== "undefined" && event?.target) ||
    document.querySelector(`button[onclick*="place_order(${preset_id}"]`);
  if (!button) {
    show_status("Error: Could not find order button", "error");
    return;
  }
  const original_text = button.textContent;

  /* We disable the submission button immediately to prevent duplicate concurrent network requests and race conditions. */
  button.disabled = true;
  button.textContent = "⏳ Processing...";
  button.classList.add("btn-processing");

  show_status(`Placing order for "${preset_name}"...`, "processing");

  try {
    const response = await fetch(`${API_BASE}/api/order`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
      },
      body: JSON.stringify({ preset_id: preset_id }),
    });

    const result = await response.json();

    if (result.success) {
      show_status(`✅ ${result.message}`, "success");
    } else {
      let message = `❌ ${result.message}`;
      if (result.cooldown_remaining) {
        const minutes = Math.floor(result.cooldown_remaining / 60);
        const seconds = result.cooldown_remaining % 60;
        message += ` (${minutes}m ${seconds}s remaining)`;
      }
      show_status(message, "error");
    }
  } catch (error) {
    show_status(`❌ Error: ${error.message}`, "error");
  } finally {
    button.disabled = false;
    button.textContent = original_text;
    button.classList.remove("btn-processing");
  }
}

async function delete_preset(preset_id) {
  if (!confirm("Are you sure you want to delete this preset?")) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/presets/${preset_id}`, {
      method: "DELETE",
      headers: { "ngrok-skip-browser-warning": "true" },
    });

    if (!response.ok) {
      throw new Error("Failed to delete preset");
    }

    show_status("Preset deleted successfully!", "success");
    load_presets();
  } catch (error) {
    show_status(`Error: ${error.message}`, "error");
  }
}

function show_status(message, type) {
  const modal = document.getElementById("status-modal");
  const message_div = document.getElementById("status-message");

  message_div.className = `status-${type}`;
  message_div.textContent = message;

  if (type === "processing") {
    const spinner = document.createElement("div");
    spinner.className = "spinner";
    message_div.appendChild(spinner);
  }

  modal.style.display = "block";

  /* Automatically dismissing the modal improves user flow by not requiring explicit dismissal for transient statuses. */
  if (type !== "processing") {
    setTimeout(() => {
      close_modal();
    }, 5000);
  }
}

function close_modal() {
  document.getElementById("status-modal").style.display = "none";
}

/* Supporting backdrop clicks provides an intuitive, standard exit interaction for modals without forcing the user to hunt for a close button. */
window.onclick = function (event) {
  const modal = document.getElementById("status-modal");
  if (event.target === modal) {
    close_modal();
  }
};

document.addEventListener("DOMContentLoaded", () => {
  load_presets();
  load_users();
  load_users_for_dropdown();
  /* Providing an initial empty row improves UX by guiding the user directly into data entry. */
  add_item_row();
});
