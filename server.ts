import express from "express";
import path from "path";
import fs from "fs";
import { execFile } from "child_process";
import { promisify } from "util";
import { createServer as createViteServer } from "vite";

const execFileAsync = promisify(execFile);

async function runDbHelper(args: string[]): Promise<any> {
  try {
    const { stdout } = await execFileAsync("python3", ["db_helper.py", ...args]);
    return JSON.parse(stdout.trim());
  } catch (err: any) {
    console.error("db_helper error:", err);
    return { error: err.message || "Execution error" };
  }
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Ensure DB is initialized on startup
  runDbHelper(["init"]).catch(err => console.error("Init DB failed:", err));

  // --- DATABASE API ROUTES ---

  app.get("/api/db/products", async (req, res) => {
    const data = await runDbHelper(["get_products"]);
    res.json(data);
  });

  app.get("/api/db/settings", async (req, res) => {
    const data = await runDbHelper(["get_settings"]);
    res.json(data);
  });

  app.post("/api/db/settings", async (req, res) => {
    const { key, value } = req.body;
    if (!key) return res.status(400).json({ error: "Missing key" });
    const data = await runDbHelper(["set_setting", String(key), String(value)]);
    res.json(data);
  });

  app.get("/api/db/stats", async (req, res) => {
    const data = await runDbHelper(["get_stats"]);
    res.json(data);
  });

  app.post("/api/db/orders", async (req, res) => {
    const { user_id, product_key, package_id, customer_data, payment_method } = req.body;
    if (!user_id || !product_key || !package_id || !customer_data || !payment_method) {
      return res.status(400).json({ error: "Missing required order fields" });
    }
    const data = await runDbHelper([
      "create_order",
      String(user_id),
      String(product_key),
      String(package_id),
      String(customer_data),
      String(payment_method)
    ]);
    res.json(data);
  });

  app.get("/api/db/orders/user/:id", async (req, res) => {
    const data = await runDbHelper(["get_user_orders", req.params.id]);
    res.json(data);
  });

  app.get("/api/db/orders/all", async (req, res) => {
    const data = await runDbHelper(["get_all_orders"]);
    res.json(data);
  });

  app.post("/api/db/orders/status", async (req, res) => {
    const { order_number, status, reason } = req.body;
    if (!order_number || !status) return res.status(400).json({ error: "Missing parameters" });
    const data = await runDbHelper(["update_order_status", String(order_number), String(status), String(reason || "")]);
    res.json(data);
  });

  app.post("/api/db/orders/receipt", async (req, res) => {
    const { order_number, receipt_file_id } = req.body;
    if (!order_number) return res.status(400).json({ error: "Missing order_number" });
    const data = await runDbHelper(["update_order_receipt", String(order_number), String(receipt_file_id || "simulated_receipt_123")]);
    res.json(data);
  });

  app.post("/api/db/orders/rate", async (req, res) => {
    const { order_number, rating, comment } = req.body;
    if (!order_number || !rating) return res.status(400).json({ error: "Missing parameters" });
    const data = await runDbHelper(["rate_order", String(order_number), String(rating), String(comment || "")]);
    res.json(data);
  });

  app.post("/api/db/orders/check_ton", async (req, res) => {
    const { order_number } = req.body;
    if (!order_number) return res.status(400).json({ error: "Missing order_number" });
    const data = await runDbHelper(["check_ton_payment", String(order_number)]);
    res.json(data);
  });

  app.post("/api/db/settings/refresh_ton_rate", async (req, res) => {
    const data = await runDbHelper(["refresh_ton_rate"]);
    res.json(data);
  });

  app.post("/api/db/packages/add", async (req, res) => {
    const { product_key, name, price_egp } = req.body;
    const data = await runDbHelper(["add_package", String(product_key), String(name), String(price_egp)]);
    res.json(data);
  });

  app.post("/api/db/packages/toggle", async (req, res) => {
    const { package_id } = req.body;
    const data = await runDbHelper(["toggle_package", String(package_id)]);
    res.json(data);
  });

  app.post("/api/db/packages/delete", async (req, res) => {
    const { package_id } = req.body;
    const data = await runDbHelper(["delete_package", String(package_id)]);
    res.json(data);
  });

  app.get("/api/db/users", async (req, res) => {
    const data = await runDbHelper(["get_users"]);
    res.json(data);
  });

  app.post("/api/db/users/ban", async (req, res) => {
    const { telegram_id, reason } = req.body;
    const data = await runDbHelper(["toggle_ban", String(telegram_id), String(reason || "")]);
    res.json(data);
  });

  app.get("/api/db/logs", async (req, res) => {
    const data = await runDbHelper(["get_logs"]);
    res.json(data);
  });

  // API Route: Get project status & .env configuration
  app.get("/api/config", (req, res) => {
    const envPath = path.join(process.cwd(), ".env");
    const examplePath = path.join(process.cwd(), ".env.example");

    let envContent = "";
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, "utf-8");
    } else if (fs.existsSync(examplePath)) {
      envContent = fs.readFileSync(examplePath, "utf-8");
    }

    res.json({
      status: "ok",
      envContent,
      botTokenSet: Boolean(process.env.BOT_TOKEN && process.env.BOT_TOKEN !== "7891234567:AAFxExampleTokenHere12345"),
      adminId: process.env.ADMIN_ID || "123456789"
    });
  });

  // API Route: Update .env configuration
  app.post("/api/config", (req, res) => {
    const { envContent } = req.body;
    if (typeof envContent === "string") {
      fs.writeFileSync(path.join(process.cwd(), ".env"), envContent);
      res.json({ success: true, message: "Configuration saved to .env" });
    } else {
      res.status(400).json({ error: "Invalid env content" });
    }
  });

  // API Route: Get Python file tree
  app.get("/api/files", (req, res) => {
    const files = [
      "main.py",
      "config.py",
      "database.py",
      "requirements.txt",
      ".env.example",
      "README.md",
      "handlers/user.py",
      "handlers/orders.py",
      "handlers/payments.py",
      "handlers/admin.py",
      "keyboards/user.py",
      "keyboards/admin.py",
      "services/ton_service.py",
      "services/payment_service.py",
      "services/scheduler_service.py",
      "services/backup_service.py",
      "services/broadcast_service.py",
      "repositories/users.py",
      "repositories/orders.py",
      "repositories/products.py",
      "repositories/settings.py",
      "repositories/admin_logs.py",
      "utils/validators.py",
      "utils/order_id.py",
      "utils/formatters.py",
      "middlewares/ban.py",
      "middlewares/maintenance.py",
      "filters/admin.py"
    ];

    const fileContents: Record<string, string> = {};
    for (const file of files) {
      const p = path.join(process.cwd(), file);
      if (fs.existsSync(p)) {
        fileContents[file] = fs.readFileSync(p, "utf-8");
      }
    }

    res.json({ files, fileContents });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
