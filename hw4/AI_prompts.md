# AI Prompts Log — Homework 4

## Problem 1: Vibe coder prompts

**Prompt 1:**

> Let's begin a new homework set. Work in the folder AI Foundations with a new subfolder called hw4. In the hw4 folder, unzip the attached file data.zip so that we have data/campus_customs.db, and data/products/. Then create a new file AI_prompts.md that will keep a log of what I type during this homework. As we go through the homework, I will call out when we move to a new problem. We are currently on problem 1. Put one section for each problem, where each section must include the problem number and title, at least one prompt that I typed, and one follow-up prompt if it is needed (and one sentence on what was lacking after the first).

**Prompt 2:**

> The title for Problem 1 is Problem 1: Vibe coder prompts. For this problem set, we will use a React + Vite + Typescript stack for front-end and a Python FastAPI backend that leverages PydanticAI agents. The goal for our homework is to create a real customer website with a helpful chatbot where shoppers can browse products, create an account, chat about merchandise, see matching items appear on the page, and get honest answers about price and stock from a local database. We will set all of this up based on our homework. This completes instructions for problem 1, we will soon move to problem 2.

**Follow-up prompt:** None needed.

**What was lacking after the first prompt:** The first prompt set up the folder, data, and log but left out the problem title and the project goals and tech stack, so Prompt 2 added them.

## Problem 2: Analyze the database

**Prompt 1:**

> Let's proceed to Problem 2: Analyze the database
>
> Please pull the database at data/campus_customs.db and explain the fields that are in each table. A visualization of the tables and database structure would be helpful. After this for the problem we will write our harness.md file

**Prompt 2:**

> Ok, let's write our harness in output/harness.md. We will start by writing out each table and its fields with a short line on why each field matters for the shop or the chatbot.
>
> Let's start with the catalogue table, which is a table that holds all of the descriptive information for our products. The product_id field in the catalogue table is critical because it is the primary key for the table and serves as a unique id for each product in the catalogue, and connects a product to the inventory table. The name, garment_type, description, colors, search_tags, image_file_path, and price fields in the table produce the information for a listing to a consumer who is on the website, and also serves as meaningful data that the chatbot can reference.
>
> The inventory table holds the details of our current inventory for the products that we stock. The id field is the unique row number for each entry in the inventory field and is the primary key for the table, and it is connected to the catalogue table by the foreign key of product_id. Each row is the size for a product, and each product has six sizes. The size field explains the size for the row, and the quantity field informs of how many units for that size of that product are in stock. This is critical information both for the consumer shopping on the site and for the chatbot seeking information on our product inventory.
>
> The users table is where we store user information when a customer creates an account. The id field is a customers unique identifier and is the primary key for the table. the name field collects a customer's full name. The email field is a customer's email, which is also unique and serves as the login id. The password_hash field is a storage of customer passwords that are hashed and have salt included. created_at is a timestamp of when the user account was made. The first_name and last_name fields serve as the first name and last name for the customer.
>
> The chat_messages table serves as the source of truth for the history of chats for the chatbot. The table includes id, which is the unique message id of the chat, and serves as the table's primary key. The table also includes user_id, which is the foreign key connecting this table to the users table so we can connect which user initiated the conversation. There is the role field, which explains if the message is from a user or the assistant. The content field contains the actual text of the message so we can audit and understand content that's coming in and out with the chatbot. The products_json field logs for assistant messages the output of catalog fields and inventory total stock that the chatbot output to the user to understand what information the assistant pulled. The created_at field is a timestamp of when the message was sent so we can reference when the conversation and message happened.

**Follow-up prompt:** _None yet._

**What was lacking after the first prompt:** _N/A_

## Problem 3: Build the Campus Customs website

**Prompt 1:**

> Great let's proceed to Problem 3: Build the Campus Customs website. We will scaffold a React + Vite + Typescript front end for Campus Customs. It should have a nav bar at the top that links to our main pages, which are the following:
>
> * Home
> * Products
> * About Us
> * Log in
> * Create account
>
> For Home, we should make the homepage simple where it starts with a banner image of Yale students at the campus customs store, and have a few sections for some of our primary catalogue categories. We should have the categories of sweatshirts, hats, and t-shirts. The sweatshirts section should display the text "Rep your school pride in chilly new england!" in all caps. The hats section should read "Hats for game day" in all caps. The t-shirts section should read "Show your spirit every day!" in all caps.
>
> For about us section, it should read some basic information about the campus customs store. It should be a professional-looking page that fits the aesthetic of the site and display information about the store. It should include the following:
> "Delivering Yale tradition for half a century.
> Our family began Campus Customs in 1975 because our father loved Yale so much, he created a Yale University memorabilia store on campus. Our entire family fell in love with the store and with Yale, so much so that we retired our father and continue to run the shop. There's no store that's more prideful, ethical, and Yale-centric.
> Our business has grown over time. We now offer embroidery, design services, large-scale screen printing, and event merchandise services.
> We've scaled so that we can deliver the experience that you deserve as a fellow Bulldog. We love New Haven and Yale University, and it's our genuine pleasure to serve you with what you need to rep your Yale school spirit.
> Come visit us at our location at 57 Broadway, New Haven, CT, 06511!"
>
> On the Products page, we should show images from the catalog. It should include the images from the image paths in the database and basic product info like name, price, and short description.
>
> Each product should open a single-item page, which includes a large image on one side and full product text on the other, including description, price, and sizes/stock. If a stock is 0 for a product size, do something to indicate that size is unavailable. Clicking a card on Products should take a shopper to this page.
>
> A chat interface should be in the bottom right of the site. A floating chat panel is fine, but it should fit the aesthetic of the site. We will set it up to talk with an agent in a later step of the homework.
>
> We can start simple with a FastAPI app in backend/main.py as we get started to serve products and images, thought we'll grow it in the agent backend in a later problem.
>
> The entire site should fit the Yale design / aesthetic using official Yale hex codes.

**Prompt 2:**

> Ok, I like the Y for the banner photo, let's keep that. What are some other product categories that we could use for sections?

**Prompt 3:**

> Ok, let's split the sections into Residential colleges, Yale Athletics, and Yale family. Residential colleges should read "Rep your school with pride!" Yale athletics should read "Bulldog athletics - top of the pack", and Yale family should read "Happily brag about your Bulldogs!" Let's follow the products page split recommendations.

**Prompt 4:**

> [Attached image: official Yale "Y" logo] Can we replace the Y in the homepage banner with this official logo? You can adapt it so that it fits the color and theme of the header

**Follow-up prompt:** _None yet._

**What was lacking after the first prompt:** _N/A_

## Problem 4: Create account and login

**Prompt 1:**

> Let's proceed to Problem 4: Create account and login
> We are going to build a normal create-account / login flow so that users can create accounts for the website. This should include:
>
> * Create account: first name, last name, email, password (with a request to confirm password, and that a match with password is required)
> * Log in: email and password.
>
> Any new account should be logged as an entry in the users table. Passwords need to be stored securely so hackers cannot access them, so they must be hashed and have a salt included in the hashed password for extra security.
>
> We already have a test user in the seed database. Their email is test@campuscustoms.yale.edu, their password is password, and the hash function is PBKDF2-HMAC-SHA256, 120,000 iterations, stored as pbkdf2_sha256$salt$hash
>
> Update the output/harness.md with how our authentication works. It should follow the security of storing a user and password with the protections we've called out above. Additionally, we should note the following:
>
> * We never un-hash the stored value. We re-hash what the user typed and compare
> * Read the salt out of the stored string, we don't make a new one at login
> * Hash the typed password with the same salt, then compare to the stored hash. Use a constant-time compare
> * Signup and login must use the same hash settings with same function, salt handling, and iteration count. If they differ, the even the right password should not match
>
> Please confirm when this is set up and the rules are logged, and I will test logging in as that user and also creating a new account for our site.

**Follow-up prompt:** _None yet._

**What was lacking after the first prompt:** _N/A_

## Problem 5: PydanticAI agent backend

**Prompt 1:**

> Great, I've tested with the test account and a new account. Let's proceed to Problem 5: PydanticAI agent backend
>
> We are going to build a shop chatbot as a PydanticAI agent behind FastAPI, and it will plug into our front-end chat widget. The API app should go in backend/main.py, which is the file we run with Uvicorn. The agent should be supported by the following:
>
> * backend/prompts/prompt.md, which is the system prompt
> * backend/agent.py, which is the agent entry and wiring
> * backend/tools.py, which are the set of tools the agent can call
> * backend/models.py, which is the Pydantic / PydanticAI structured types
>
> In main.py, we will expose a chat route so that a message from the website returns a reply from the agent. We should leverage our API key for this.
>
> In prompts/prompt.md, we will store the Campus Customs voice and safety basics. We should leverage a helpful agent voice that is full of school spirit and is very informed about Yale Bulldogs. The agent should be full of school spirit but most of all help customers not only get an answer to their question, but provide helpful insights to them based on their question (for instance, if a customer asks about a shirt in small, the agent can provide insight into if that shirt is in or out of stock in that size, the price of that item, and a link to that item). Additionally, if a customer doesn't ask about a specific item but is looking for recommendations, the agent can make helpful insights based on the customer. In terms of safety, the chatbot should never communicate any harmful information, should never encourage a customer to make a purchase they're not comfortable with, and should never use curse words or dirty or inappropriate language. The chatbot should always be positive and helpful. The chatbot should never output any customer information / pii info.
>
> Any start or update types for chat replies and product cards should be stored in models.py.
>
> Please log the voice of the agent into output/harness.md. Additionally, note in the harness how the front end talks to FastAPI and how the agent is loaded with the prompt file and model. Based on a user message to the chatbot, the chatbot should pull supporting information from our database from the catalogue and inventory tables as best it can interpret from the user message and should leverage the prompt.md file for information about the voice and safety basics, and use the pydanticai in models.py to fire with the backend.
>
> The backend should run from the backend/ folder like this:
> uvicorn main:app --reload --port 8000

**Follow-up prompt:**

> Yes let's update it that any values of stock less than or equal to 5 are considered "low stock". Once a conversation starts, it should be logged to the chat_messages table. Please confirm when this is ready and we'll proceed to the next question

**What was lacking after the first prompt:** The first prompt didn't define a "low stock" threshold (so the agent didn't always flag 5 units as low) or require conversations to be saved to the chat_messages table.

## Problem 6: Tools: product info and stock

**Prompt 1:**

> Great, let's proceed to Problem 6: Tools: product info and stock
>
> We are going to give the agent tools that will allow it to look up real information from campus_customs.db
>
> The first tool should be "Product Confirmation". When a customer asks about a product, the agent should query the campus_customs.db database, specifically the "description" field of the catalogue table, and find the best match from the available descriptions to match the user's inquiry with the chatbot. This should also pick up that product's "name". The agent should return the product name to the customer in quotations and then ask "Is this the item you're inquiring about?" with a Yes/No selection. If a customer selects No, the agent should prompt the user to provide more details, and when the user responds, it should restart the Product Confirmation tool using the new information provided. If the user selects Yes, the agent should ask if the customer is asking about a specific size, with a Yes/No selection. If the customer selects "Yes", there should be another prompt from the chatbot with our size options of XS, S, M, L, XL, XXL, where the customer can select one option. This option will then be leveraged for the next tool. If a customer selects "No", we will show inventory for all available sizes of that product.
>
> The second tool is "Information Output". When the agent has completed the Product Confirmation tool with a product name validated by the customer, the agent will then use the product_id for the same product that was validated by the customer, and will use the database information for that product_id for the following fields: "price" in the catalogue table, and "quantity" in the inventory table. If a user selected a specific size, the agent should only produce the "quantity" for the product_id where the specific size was selected. If a user responded "no" to a specific size, the agent should return the quantity for every size of that product_id, broken out by size. If a quantity is 0, the agent should return "0 - Sold Out". If the agent cannot find the price or inventory by querying the database, it should never make up values. It should query the database for a match, or if it cannot find a match after 30 seconds, it should halt and report a timeout issue, at which point the user can ask it to try again.
>
> In prompts/prompt.md, the agent should ask these questions to a customer in the chatbot, starting with the question, "Are you asking about a specific product? If so, please describe the item." If a customer replies with a product description, call the "Product Confirmation" agent. As described in the agent, the "Information Output" tool should be called at completion of the "Product Confirmation" agent.
>
> Return types should be added or updated as necessary for these tools in models.py.
>
> In output/harness.md, I want to explicitly call out the two tools by name that I've described and explain the models feels. Please write the following in the harness. "The first tool that we're adding is 'Product Confirmation', which is meant to validate the product that a customer is inquiring about. The tool leverages the name, description, and product_id fields in the catalogue table to validate if what a customer is inputting is a correct understanding of what is being asked about by the customer and matches our database information. The second tool that we're adding is 'Information Output', which is meant to pull the price and inventory for the validated product. It leverages the product_id, quantity, price, and size fields in the inventory and catalogue tables to gather the price and inventory for the same product that's been confirmed."

**Follow-up prompt:** _None yet._

**What was lacking after the first prompt:** _N/A_

## Problem 7: Chat search that updates the page

**Prompt 1:**

> Let's proceed to Problem 7: Chat search that updates the page
>
> We're going to add a new tool called "Product Preview" for the agent. This tool should be called when a customer is asking about a type of time, like an example of "what hoodies do you have?" When this type of question is asked, the agent should call on the same campus_customs.db and should search the catalogue table for the most appropriate match of "garment_type". It should then begin to dynamically load product cards on the website. The agent should match the inquiry to garment_type and show product cards that show image (the "image" field), name (the "name") field, price (the "price" field), and short info (the "description" field) from the catalogue table. The front end should then render those as product cards on the website. If a user clicks on the product card, it should load the same single-item page behavior that we previously defined with a detail view (the single-page behavior from problem 3).
>
> Please updated prompts/prompt.md to reflect this new behavior, tools.py so that the tool is captured, and output/harness.md to document this new behavior. Please also include in our logging that for token efficiency, we should include a maximum of 6 product cards for a user request with this tool. If the chatbot query cannot find a product type, it should return to the user, "I cannot locate this type of product. Is there another type of product you're looking for?"

**Follow-up prompt:** (noticed during later testing)

> For problem 7, when i ask about hoodies, i have to change pages to see the list of hoodies. Can you fix this so that the page automatically updates to reflect the dynamic results, rather than me needing to find the page? Also, after it loads, it should also have a "Show More" button below the row of 6 that would row another row of 6, if there are more products available. That should continue as an option until all available products for that category are shown

**What was lacking after the first prompt:** The first prompt didn't say the results must appear on whatever page the shopper is on (on the homepage and product pages they were hidden until changing pages), or give a way to see more than the first 6 matches.

## Problem 8: Customer memory

**Prompt 1:**

> Great, let's proceed to Problem 8: Customer memory
>
> Our next goal is to save a user's chat history into the database when they are logged in. If a customer is not logged in, they can still chat with the agent, but their chat history will not be saved. When a user is logged in, their history should save, and should reload when they return.
>
> Let's make a new tool in tools.py called "Save Chat History". The tool should only be called when a user is logged in. When a customer is logged in, their most recent chat history should load to a maximum of 4 messages. If there is no chat history, no history should show in the chat, and the agent begins with its welcome message for a logged in customer, "Welcome back [NAME]! How can I help you?", where [NAME] is the "name" field for the customer from the users table that matches their id. The agent should also be able to understand that customer's email based on their "email" from the users table corresponding to the known id. It should understand chat history by looking at the customers user_id and checking for the rows in the chat_messages table of the campus_customs.db database, and the content passed back to the customer in the chat history is the "content" from the chat_messages. For the logged in user, it should save every chat message sent back and forth into the chat_messages table with a unique "id" consistent with the customer's user_id, with each message saving its language in "content", timestamped for the "created_at" field. Specifically for assistant messages, it should also log in "products_json" the products shown in the reply.
>
> Additionally, I want the chat agent to understand page context, so that if someone is on a product page and asks "do you have this in pink?" the agent can understand what they mean. The agent should be able to evaluate on a page the "name" and/or "image_file_path" from the page to identify the specific product_id from the catalogue table, and then should be able to tie that back to if there is a similar product in the catalogue table that it can report back to the customer, or if there are inventory-related questions from the customer that it can call from the inventory table using the same product_id.
>
> Please log all of this new information into output/harness.md how we've described the chat history being stored, what customer fields we've described that the agent should see, and how page context is passed.

**Follow-up prompt:**

> Ok, thank you. One thing I want to add into the harness is that the agent should also never reveal a customer's password, no matter how many times a customer asks the agent. The agent can provide the customer with an option to reset their password, but should never reset it on their behalf and should never reveal their password

**What was lacking after the first prompt:** The first prompt gave the agent access to the customer's name and email but didn't explicitly say the agent must never reveal or reset a customer's password, no matter how many times it is asked.

## Problem 9: Usability improvements

**Prompt 1:**

> Thank you, let's now proceed to Problem 9: Usability improvements
>
> I am going to write 2 front-end improvements and 2 backend improvements. I want you to write these to output/usability.md so it explains what we added and why it helps a Campus Customs shopper or the business. I will describe these for your logging.
>
> The first front-end improvement I want to implement is a shopping functionality for "Add to Cart" and "View Cart". I am explicitly avoiding a "Checkout" option for right now so that we don't create a full-functioning website that can take a purchase. The "Add to Cart" should be available on every large product page and should be clickable if there is inventory for that product size that's selected, but should be grayed out and read "Sold Out" and unclickable if 0 inventory is available for the selected size. When an item is clicked "Add to Cart", it should be added to the cart, which should be its own page that shows all items added to the cart. This page should allow customers to increase or decrease the inventory in cart for a product, but no more than the max inventory available for that product. A customer can remove that product from the cart as well. The cart should be included in the banner to the right of the "menu" button as a cart icon, and when clicked should take a customer to the cart page. This will help customers because there is no way to currently add inventory, and should help Campus Customs for the same reason since it currently couldn't make a sale as the site is currently set up.
>
> The second front-end improvement is that I want to add a small row to the bottom of the page that shows "Your Recent Picks" so that you can see the 5 most recent products that you've clicked into to see the large product page. The row should be sticky to the bottom of the page and update to reflect the 5 most recently viewed products that you've clicked on. This should be included to keep a customer's recently visited products top-of-mind, which may help with our purchase conversions for Campus Customs.
>
> The first backend improvement that I want to make is that the chatbot agent should never log a customer's password if they type it in. We've created several guardrails and safety requirements for the agent, but if a customer enters their password there, it would be saved in the chat history. We should explicitly never store a customer's password from a chat message so that we avoid any data privacy issues and keep data protection extremely high.
>
> The second backend improvement is that I want to make is getting greater product understanding from our database. When I asked the agent "do you have anything in green?", it was searching for a specific product to match. I want it to do a more general search of our catalogue when the question from a customer is not about a specific product like "do you have this in pink"? If not about a specific product, I want the agent to use a new tool of "General Inquiry", which should first be able to understand what the customer is asking about. For example, is the customer asking about an order, a color, a product type, etc. If asking about a color, it should query our catalogue table for products that match that color using the "colors" field. If it's asking about a product type or category, it could query against "garment_type" or "search_tags" for general metadata about the products. Generally, it should look for best matches of a product or response based on the ask. The tool should never act for longer than 12 seconds before timing out for efficiency purposes. This will help a shopper so they can better find products they're looking for, and for the business so that we don't burn tokens on long queries.

**Follow-up prompt:**

> Great, thank you. Let's tie a customer's cart to their account so that if they're logged in and adjust their cart, that cart follows them across devices and sessions. Please confirm when this is ready

**What was lacking after the first prompt:** The first prompt's cart was saved only in the shopper's browser, so it didn't follow a logged-in customer to another device or a later session.

**Follow-up prompt 2:** (added during Problem 10 testing; it belongs with the Problem 9 usability improvements)

> Thank you. Can we also add a self-serve password reset functionality for the site? I should have logged this for problem 9 for usability but noticing it now during testing. please log it to the harness as well that a customer can password reset.

**What was still lacking:** The usability improvements didn't include a way for a customer to reset a forgotten password themselves; the chatbot could only point them to the store.

## Problem 10: Style the website

**Prompt 1:**

> Great, let's proceed to Problem 10: Style the website
>
> I want to adapt the design of the website so that it really makes clear that it is a shop for an ivy league college. The font should be sophisticated. The colors should continue to resonate with Yale's colors for school pride. The motion should feel sleek and advanced, with sections loaded upon scroll and a scroll feel like you're landing on a new section, rather than being a continuous scroll. Because some of the images are on a black background and some are on a white background, we should make it consistent that images are on a white background when presented on the site. We should have fun and Yale-spirited expressions when you scroll to a new section (for instance, it could pop up on top of the section "BOOLA BOOLA!" for a second, or show an animated gif of Handsome Dan eating the Harvard pennant for a second, for example. When loading to a new screen, an animated gif of Handsome Dan the bulldog should overlay on top of the page with him doing something funny or school-spirited. The sections on the homepage should have an ai-generated image next to the products that is appropriate for the section (for example, the section about sports should show Yale athletes celebrating at a game, and next to the image are the preview tiles for the section). When a customer adds a product to their cart, Handsome Dan should pop up and say something encouraging like "Great Choice!" or "Looks Good!" or "I'd Chew That!" The site should also be mobile-friendly.
>
> Please log in output/design.md a summary of these changes to the site, with the reasoning being that making the site feel more professional, connected to Yale, and fun should generally resonate with our target audience of Yale students and their families, and should encourage them to stay on the site for longer and make a purchase.

**Follow-up prompt:**

> The product tiles on sections now have very small image sizes. Can you resize the tiles so that its sized to show more of the image?

**What was lacking after the first prompt:** The first prompt asked for full-screen sections with an image beside the product tiles but didn't say how large the product photos should be, so fitting four tiles on one screen left the product images too small.

**Follow-up prompt 2:**

> I see it resized, but on laptop it still feels like a lot of empty space in the top part of the box. can we make the tiles 2 rows of 3 tiles, so that the tiles are less wide but the same height? I want to see less white space for the tiles.
>
> Also, some of the images are still on a black background. I am wondering if this is because the images are png files with a transparent background. If that's the case, add a white background to the images so that they look more purposeful on the page. Additionally, some of the updated images have mostly white background and black bars on the edges. resolve this so the background is completely white

**What was still lacking:** The wider tiles left empty space around the square product photos, and the first white-background pass missed some photos (transparent images showing as black, and black bars that weren't pure black).

**Follow-up prompt 3:**

> Thanks. One more for this question. The "Create an Account" page has an issue where the Last Name field input box extends beyond the box on the page. Can you resolve this so that all requested fields fit in the box?

**What was still lacking:** The restyle didn't check the form layouts, and the side-by-side First/Last name inputs kept the browser's default minimum width, so the Last Name box overflowed the card.

## Problem 11: Site testing (app testing)

**Prompt 1:**

> [Attached three screenshots: "Chat Inventory Check", "Dynamic Tiles for Quarter Zips", and "Usability - No Password Communication"] Ok, let's proceed to Problem 11: Site testing (app testing)
>
> I am attaching three images, which I want you to store in output/app_check_images/
>
> Then I want you to create output/app_check.html, which is what I'll use to document what I've tested on the site. The HTML should have a heading for each check, a screenshot (one of the appropriate screenshots), and one or two sentences on what the screenshot provides. The screenshot image in the html should have a relative path based on how the screenshot is stored.
>
> The first check is "Chat checking the inventory level of an item". The appropriate screenshot is the screenshot "Chat Inventory Check". The screenshot shows me looking at the Benjamin Franklin Fleece Jacket and asking about how many Larges are in stock for that product. The chat returns that there are 2 Larges for this product, calls out that it's low stock, and also displays its price.
>
> The second check is "Dynamic search-result cards". The appropriate screenshot is the screenshot "Dynamic Tiles for Quarter Zips". The screenshot shows me asking the chat if we have any quarter zips available, at which point the page refreshes to show all of the tiles for products categorized as quarter zips.
>
> The third check is "Usability feature - no password communication". The appropriate screenshot is the screenshot "Usability - No Password Communication". The screenshot shows me repeatedly asking the chat what my password is, which I requested that the agent never do. Instead, the agent communicates that it cannot relay the password, and that a user can self-reset their password, which I also built into the website.

**Follow-up prompt:**

> I'm not able to laod the app_check.html. Can you load it for me to view the output?

**What was lacking after the first prompt:** The first prompt created the HTML file but didn't include a way to open and view it, so it needed to be served and loaded in the browser preview.

## Problem 12: Audit trail, safety, finish harness

**Prompt 1:**

> Great, let's proceed to Problem 12: Audit trail, safety, finish harness
>
> Create an append-only output/audit_trail.json of agent-loop activity (time, tool name, short args/result, stop reason). Do not wipe this between runs.
>
> Log the following safety rules for the agent in prompts/prompt.md. For the audit trail, never make up values. The audit log should capture your agent activity with the actual values used. If a loop takes longer than 30 seconds, flag that to me (NEVER to a customer) so we can find efficiency gains and troubleshoot. If you're creating a new tool that we didn't build and calling it somehow, also flag that to me (NOT to a customer) so I can understand what non-approved processes you would be trying to leverage.
>
> Then, finish up the harness at output/harness.md so that it's readable for a business owner to understand how the system works. It should include:
>
> * Model fields in models.py and why we chose them
> * Tools and abilities
> * Safety rules
> * Specs (loop limits, result caps, models, how to run front + back)

**Follow-up prompt:** _None yet._

**What was lacking after the first prompt:** _N/A_

## Problem 13: Push to GitHub and submit the URL

**Prompt 1:**

> Let's proceed to Problem 13: Push to GitHub and submit the URL
>
> Put all of our code in a folder named hw4 and push it to a GitHub repository (the GitHub that's linked to this Claude account). It must be a public repository. Make sure to not put the real .env, campus_customs.db, or product images in the GitHub repo. Use .gitignore. Include .env.example with placeholders only.
>
> The agent itself should be four files under backend/
>
> * prompts/prompt.md
> * agent.py
> * tools.py
> * models.py
>
> The README.md should explain how to run the front end and back end after placing the data pack.

**Follow-up prompt:**

> For /backend/, there are several .py files that should be part of either agent.py, models.py, tools.py. For files like auth.py, cart.py, mailer.py, password_reset.py, and privacy.py, can you add them to the most appropriate backend folder between agent.py, models.py, or tools.py? Which I imagine is in tools.py

**What was lacking after the first prompt:** The first prompt asked for the agent to be four files but didn't say where the supporting modules (auth, cart, mailer, password reset, privacy) should live, so they were left as separate backend files.

**Follow-up prompt 2:**

> Yes, commit and push the backend restructure to the GitHub repo.

**What was still lacking:** The restructure was finished and tested locally, but the public GitHub repo still had the old file layout until it was committed and pushed.

**Follow-up prompt 3:**

> ok, thank you. .env.example and requirements.txt also shouldn't be in /backend, but should be directly in hw4 (it should be hw4/requirements.txt, rather than hw4/backend/requirements.txt).

**What was still lacking:** The earlier prompts didn't say where the project-level setup files belong, so requirements.txt and .env.example were left in backend/ instead of the top of hw4/.

**Follow-up prompt 4:**

> Yes, commit and push moving requirements.txt and .env.example into hw4/.

**What was still lacking:** The move was made and tested locally but not yet published, so the GitHub repo still showed the files under backend/.
