# Data pack goes here

The database and product images are **not** stored in this repository. After cloning, unzip the course data pack (`data.zip`) into this folder so it looks like:

```
hw4/data/
├── campus_customs.db      # SQLite database: catalogue, inventory, users, chat_messages
└── products/              # product photos (*.jpg), referenced by catalogue.image_file_path
```

When the backend starts, it adds two tables to the database automatically (`cart_items` and `password_resets`).

Optional: run `backend/scripts/whiten_images.py` to create `data/products_white/` (every photo on a white background); the backend serves those copies automatically when they exist. See the main README.
