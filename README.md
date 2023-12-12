# Daraz-web-scraped-Mobile-Product-Analysis-Interactive-Chatbot-System-with-MySQL-database-and-Flask
<br>This notebook contains an entire project that involves sophisticated web scraping of mobile products from daraz.pk, data storage, and the development of an advanced chatbot. The project will focus on extracting detailed information about mobile products, creating an intelligent chatbot for user interaction, and presenting the data through an insightful and interactive dashboard.<br/>
<br>key tasks:<br/>
<br>WEB SCRAPING:<br/>
<br>Objective: Extract mobile product data from daraz.pk, from the first five pages.<br/>
<br>Example: Using Selenium a script is written to navigate to the mobile phone section of daraz.pk. This script would then parse through the HTML of each page, extracting product details like name, price, brand, and reviews. For instance, if a product is named "Samsung Galaxy S21," script would extract its price, specifications, and user reviews. Extract essential information such as product ID, name, price, and company. Extract reviews for each product, including review ID, score, and content. Store product details and reviews in separate files (excel or csv), uniquely identifying with an id<br/>
<br>Key Focus: Filtering out irrelevant products. You could achieve this by setting conditions to exclude listings that contain keywords like "case," "cover," or "charger."<br/>



<br>Database Integration:<br/>
<br>Objective: Create a structured storage system for the scraped data.<br/>
<br>Example: If using MySQL, you would design tables such as Products (storing ID, name, price, brand) and Reviews (storing review text, rating, associated product ID). This allows for efficient querying and analysis of data.<br/>
<br>Key Focus: Ensure the database schema is robust enough to handle various types of data and queries, such as retrieving all products within a certain price range or the average rating of a brand.<br/>



<br>Chatbot Development:<br/>
<br>Objective: Develop a chatbot that can handle user queries based on the scraped data.<br/>
<br>Example: If a user asks, "What is the best phone under $300?" your chatbot, using the stored data, should be able to analyze and respond with options like "Based on user ratings and price, the best phones under $300 are [Product A], [ProductB]."<br/>
<br>Key Focus: Implement natural language processing (NLP) capabilities for the chatbot to understand and accurately respond to complex queries.<br/>

<br>Dashboard Development:<br/>

<br>Objective: Create a dashboard to visually present the scraped data.<br/>
<br>Elements with Examples:<br/>
<br>■ Input field for querying data (chatbot)<br/>
<br>■ Total number of listings.<br/>
<br>■ Average product price.<br/>
<br>■ Average ratings of products.<br/>
<br>■ Average review count per product.<br/>
<br>■ Total number of questions asked.<br/>
<br>■ Top 5 products based on defined criteria (e.g., highest ratings, most reviews) A dynamic section showcasing the top 5 mobile phones based on a selected criterion like highest rating or most reviews. Each product would have a visual representation of a clickable link.<br/>
<br>■ Make product details clickable with URLs linking back to the respective product on daraz.pk.<br/>
<br>■ Use Flask frontend technology to make this dashboard.<br/>
