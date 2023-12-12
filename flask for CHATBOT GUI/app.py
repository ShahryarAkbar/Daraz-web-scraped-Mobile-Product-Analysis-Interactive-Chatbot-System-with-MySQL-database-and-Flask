from flask import Flask, render_template, request
import mysql.connector
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import re

app = Flask(__name__)

# Connect to MySQL database
def connect_to_database():
    try:
        connection = mysql.connector.connect(
             host="localhost",
            user="root",
            password="Dodokaka@786",
            database="dstt_project"
        )
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Disconnect from MySQL database
def disconnect_from_database(connection):
    if connection:
        connection.close()

# Execute a query in the database
def execute_query(query, connection, parameters=None):
    cursor = connection.cursor(dictionary=True)
    
    if parameters:
        cursor.execute(query, parameters)
    else:
        cursor.execute(query)
    
    result = cursor.fetchall()
    cursor.close()
    return result


def generate_response(prompt, model, tokenizer, max_length=50):
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    output = model.generate(input_ids, max_length=max_length, num_beams=5, no_repeat_ngram_size=2, top_k=50, top_p=0.95, temperature=0.7)
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return response


def process_above_query(user_query, connection):
    above_match = re.search(r'(?:over|above) (\$?[\d,]+)', user_query)
    if above_match:
        budget_str = above_match.group(1).replace(',', '')
        try:
            budget = float(budget_str)
        except ValueError:
            return "I couldn't understand the budget. Please provide a valid budget."
        
        if not (19499 <= budget <= 267000):
            return "Please provide a budget within the valid range of $19499 to $267000."

        return execute_above_query(connection, budget)
    else:
        return "I'm not sure how to respond to that. If you have a specific question or request, feel free to let me know!"

def execute_above_query(connection, budget):
    query = f"""
        SELECT 
            pd.Title, 
            MIN(pd.Price) as Price,
            IFNULL(MIN(pd.Ratings), 0) as MinRatings,
            COUNT(DISTINCT pr.Review_text) as TotalReviews
        FROM 
            product_details pd
        LEFT JOIN 
            product_reviews pr ON pd.Title = pr.Title
        WHERE 
            pd.Price > {budget + 20000}
        GROUP BY 
            pd.Title, pd.Price, pd.Ratings
        ORDER BY 
            TotalReviews DESC
        LIMIT 3
    """
    query_result = execute_query(query, connection)
    
    total_price = 0
    total_rating = 0
    total_products = 0

    response = []
    if query_result:
        response.append("Based on user ratings and price, the best phones above PKR {0} are:<br>".format(budget))
        for product in query_result:
            # Create a Daraz search link
            daraz_link = f"https://www.daraz.pk/catalog/?q={'+'.join(product['Title'].split())}&_keyori=ss&from=input&spm=a2a0e.home.search.go.35e3407617mRpH"

            product_str = (
                "<div class='product-info'>"
                "<p><a href='{0}' target='_blank'>{1}</a></p>".format(daraz_link, product['Title']) +
                "<p>Price: PKR {0:.2f}</p>".format(product['Price']) +
                "<p>Ratings: {0}</p>".format(product['MinRatings']) +
                "<p>Total Reviews: {0}</p>".format(product['TotalReviews']) +
                "</div><br>"
            )


            response.append(product_str)

            # Accumulate values for average calculation
            total_price += product['Price']
            total_rating += product['MinRatings']
            total_products += 1
    
    # Calculate averages
    average_price = total_price / total_products if total_products > 0 else 0
    average_rating = total_rating / total_products if total_products > 0 else 0

    # Display averages at the end
    response.append("<br>Average Price of All Products: PKR {:.2f}<br>".format(average_price))
    response.append("Average Rating of All Products: {:.2f}<br>".format(average_rating))

    return "".join(response)

def process_specification_query(user_query, connection):
    specification_match = re.search(r'with (.+?) and (.+)', user_query)
    if specification_match:
        camera_spec = specification_match.group(1).strip()
        ram_spec = specification_match.group(2).strip()

        return execute_specification_query(connection, camera_spec, ram_spec)
    else:
        return "I'm not sure how to respond to that. If you have a specific question or request, feel free to let me know!"

def process_range_query(user_query, connection):
    range_match = re.search(r'between (\d+) and (\d+)', user_query) or re.search(r'(\d+) to (\d+)', user_query)
    if range_match:
        lower_budget = float(range_match.group(1))
        upper_budget = float(range_match.group(2))
        print(f"Detected range query: {lower_budget} to {upper_budget}")
        response_list = execute_range_query(connection, lower_budget, upper_budget)

        # Combine the formatted responses into a single string
        formatted_response_str = "\n".join(response_list)

        print(f"Response from range query: {formatted_response_str}")
        return formatted_response_str
    else:
        return "I'm not sure how to respond to that. If you have a specific question or request, feel free to let me know!"

def process_condition_query(user_query, connection):
    # Extract conditions from the user input
    price_match = re.search(r'less than (\$?[\d,]+)', user_query)
    rating_match = re.search(r'rating greater than (\d+(\.\d+)?)', user_query)
    brand_match = re.search(r'(.+) brand', user_query)

    # Extract values from matches
    max_price = float(price_match.group(1).replace(',', '')) if price_match else None
    min_rating = float(rating_match.group(1)) if rating_match else None
    brand = brand_match.group(1) if brand_match else None

    # Calculate the minimum price based on the provided maximum price
    min_price = max(0, max_price - 20000)

    return execute_condition_query(connection, min_price, max_price, min_rating, brand)

def process_company_mobiles_query(user_query, connection):
    company_match = re.search(r'company (\w+)', user_query, re.I)

    if company_match:
        company = company_match.group(1).strip().lower()
        return execute_company_mobiles_query(connection, company)
    else:
        return "I'm not sure how to respond to that. If you have a specific question or request, feel free to let me know!"


def execute_company_mobiles_query(connection, company):
    # Build a query to find all mobiles of a specific company
    query = f"""
        SELECT 
            pd.Title, 
            MIN(pd.Price) as Price,
            IFNULL(MIN(pd.Ratings), 0) as MinRatings,
            COUNT(DISTINCT pr.Review_text) as TotalReviews
        FROM 
            product_details pd
        LEFT JOIN 
            product_reviews pr ON pd.Title = pr.Title
        WHERE 
            pd.Title LIKE '%{company}%'
        GROUP BY 
            pd.Title, pd.Price
        ORDER BY 
            TotalReviews DESC, MinRatings DESC
        LIMIT 8
    """

    query_result = execute_query(query, connection)

    total_price = 0
    total_rating = 0
    total_products = 0

    response = []
    if query_result:
        response.append(f"All smartphones of {company}:<br>")
        for product in query_result:
            # Create a Daraz search link
            daraz_link = f"https://www.daraz.pk/catalog/?q={'+'.join(product['Title'].split())}&_keyori=ss&from=input&spm=a2a0e.home.search.go.35e3407617mRpH"

            response.append(f"<br>Title: <a href='{daraz_link}' target='_blank'>{product['Title']}</a><br>")
            response.append(f"Price: PKR {product['Price']:.2f}<br>")
            response.append(f"Ratings: {product['MinRatings']}<br>")
            response.append(f"Total Reviews: {product['TotalReviews']}<br>")

            # Accumulate values for average calculation
            total_price += product['Price']
            total_rating += product['MinRatings']
            total_products += 1

        # Calculate averages
        average_price = total_price / total_products if total_products > 0 else 0
        average_rating = total_rating / total_products if total_products > 0 else 0

        # Display averages at the end
        response.append(f"<br>Average Price of All Products: PKR {average_price:.2f}<br>")
        response.append(f"Average Rating of All Products: {average_rating:.2f}<br>")

    else:
        response.append(f"No smartphones found for {company}.")

    return "".join(response)



def execute_condition_query(connection, min_price=None, max_price=None, min_rating=None, brand=None):
    # Build a query to find phones based on conditions
    where_conditions = []

    if max_price is not None:
        where_conditions.append(f"pd.Price <= {max_price}")

    if min_price is not None:
        where_conditions.append(f"pd.Price >= {min_price}")

    if min_rating is not None:
        where_conditions.append(f"IFNULL(pd.Ratings, 0) >= {min_rating}")

    if brand is not None:
        where_conditions.append(f"pd.Title LIKE '%{brand}%'")

    where_clause = " AND ".join(where_conditions)

    query = f"""
        SELECT 
            pd.Title, 
            MIN(pd.Price) as Price,
            IFNULL(MIN(pd.Ratings), 0) as MinRatings,
            COUNT(DISTINCT pr.Review_text) as TotalReviews
        FROM 
            product_details pd
        LEFT JOIN 
            product_reviews pr ON pd.Title = pr.Title
        {'WHERE ' + where_clause if where_conditions else ''}
        GROUP BY 
            pd.Title, pd.Price, pd.Ratings
        ORDER BY 
            TotalReviews DESC
        LIMIT 3
    """

    query_result = execute_query(query, connection)

    total_price = 0
    total_rating = 0
    total_products = 0

    response = []
    if query_result:
        # Generate and return the response
        for product in query_result:
            # Create a Daraz search link
            daraz_link = f"https://www.daraz.pk/catalog/?q={'+'.join(product['Title'].split())}&_keyori=ss&from=input&spm=a2a0e.home.search.go.35e3407617mRpH"

            product_str = (
                f"Title: <a href='{daraz_link}' target='_blank'>{product['Title']}</a><br>"
                f"Price: PKR {product['Price']:.2f}<br>"
                f"Ratings: {product['MinRatings']}<br>"
                f"Total Reviews: {product['TotalReviews']}<br><br>"
            )

            response.append(product_str)

            # Accumulate values for average calculation
            total_price += product['Price']
            total_rating += product['MinRatings']
            total_products += 1

    # Calculate averages
    average_price = total_price / total_products if total_products > 0 else 0
    average_rating = total_rating / total_products if total_products > 0 else 0

    # Display averages at the end
    response.append(f"<br>Average Price of All Products: PKR {average_price:.2f}<br>")
    response.append(f"Average Rating of All Products: {average_rating:.2f}<br>")

    return "".join(response)


def execute_range_query(connection, lower_budget, upper_budget):
    print(f"Executing range query: {lower_budget} to {upper_budget}")
    if lower_budget > upper_budget:
        lower_budget, upper_budget = upper_budget, lower_budget
    query = f"""
        SELECT 
            pd.Title, 
            MIN(pd.Price) as Price,
            MIN(pd.Ratings) as MinRatings,
            COUNT(DISTINCT pr.Review_text) as TotalReviews
        FROM 
            product_details pd
        LEFT JOIN 
            product_reviews pr ON pd.Title = pr.Title
        WHERE 
            pd.Price >= {lower_budget} AND pd.Price <= {upper_budget}
        GROUP BY 
            pd.Title, pd.Price, pd.Ratings
        ORDER BY 
            TotalReviews DESC
        LIMIT 3
    """

    query_result = execute_query(query, connection)

    total_price = 0
    total_rating = 0
    total_products = 0

    response = []
    if query_result:
        # Generate and return the response
        for product in query_result:
            # Create a Daraz search link
            daraz_link = f"https://www.daraz.pk/catalog/?q={'+'.join(product['Title'].split())}&_keyori=ss&from=input&spm=a2a0e.home.search.go.35e3407617mRpH"

            product_str = (
                f"Title: <a href='{daraz_link}' target='_blank'>{product['Title']}</a><br>"
                f"Price: PKR {product['Price']:.2f}<br>"
                f"Ratings: {product['MinRatings']}<br>"
                f"Total Reviews: {product['TotalReviews']}<br><br>"
            )

            response.append(product_str)

            # Accumulate values for average calculation
            total_price += product['Price']
            total_rating += product['MinRatings']
            total_products += 1

    # Calculate averages
    average_price = total_price / total_products if total_products > 0 else 0
    average_rating = total_rating / total_products if total_products > 0 else 0

    # Display averages at the end
    response.append(f"<br>Average Price of All Products: PKR {average_price:.2f}<br>")
    response.append(f"Average Rating of All Products: {average_rating:.2f}<br>")

    return response


def execute_specification_query(connection, camera_spec, ram_spec):
    query = f"""
        SELECT
            pd.Title, 
            MIN(pd.Price) as Price,
            IFNULL(MIN(pd.Ratings), 0) as MinRatings,
            COUNT(DISTINCT pr.Review_text) as TotalReviews
        FROM 
            product_details pd
        LEFT JOIN 
            product_reviews pr ON pd.Title = pr.Title
        WHERE 
            pd.Title LIKE '%{camera_spec}%' AND pd.Title LIKE '%{ram_spec}%'
        GROUP BY 
            pd.Title
        ORDER BY 
            TotalReviews DESC
        LIMIT 3
    """

    query_result = execute_query(query, connection)

    total_price = 0
    total_rating = 0
    total_products = 0

    response = []
    if query_result:
        response.append(f"Based on your specifications, here are some mobiles:<br>")
        for product in query_result:
            # Create a Daraz search link
            daraz_link = f"https://www.daraz.pk/catalog/?q={'+'.join(product['Title'].split())}&_keyori=ss&from=input&spm=a2a0e.home.search.go.35e3407617mRpH"

            response.append(f"<br>Title: <a href='{daraz_link}' target='_blank'>{product['Title']}</a><br>")
            response.append(f"Price: PKR {product['Price']:.2f}<br>")
            response.append(f"Ratings: {product['MinRatings']}<br>")
            response.append(f"Total Reviews: {product['TotalReviews']}<br>")

            # Accumulate values for average calculation
            total_price += product['Price']
            total_rating += product['MinRatings']
            total_products += 1

    # Calculate averages
    average_price = total_price / total_products if total_products > 0 else 0
    average_rating = total_rating / total_products if total_products > 0 else 0

    # Display averages at the end
    response.append(f"<br>Average Price of All Products: PKR {average_price:.2f}<br>")
    response.append(f"Average Rating of All Products: {average_rating:.2f}<br>")

    return "".join(response)


def process_brand_budget_query(user_query, connection):
    brand_budget_match = re.search(r'brand (\w+) upto (\d+)', user_query, re.I)

    if brand_budget_match:
        brand = brand_budget_match.group(1).strip().lower()
        budget = int(brand_budget_match.group(2))

        return execute_brand_budget_query(connection, brand, budget)
    else:
        return "I'm not sure how to respond to that. If you have a specific question or request, feel free to let me know!"  

def execute_brand_budget_query(connection, brand, budget):
    # Consider a price range from (budget - 20000) to the specified budget
    min_price = max(0, budget - 20000)
    
    # Build a query to find smartphones of a specific brand within the specified budget range
    query = f"""
        SELECT 
            pd.Title, 
            pd.Price,
            IFNULL(MIN(pd.Ratings), 0) as MinRatings,
            COUNT(DISTINCT pr.Review_text) as TotalReviews
        FROM 
            product_details pd
        LEFT JOIN 
            product_reviews pr ON pd.Title = pr.Title
        WHERE 
            pd.Title LIKE '%{brand}%'
            AND pd.Price >= {min_price} AND pd.Price <= {budget}
        GROUP BY 
            pd.Title, pd.Price
        ORDER BY 
            TotalReviews DESC, MinRatings DESC
    """

    query_result = execute_query(query, connection)

    if query_result:
        response = f"All smartphones of {brand} up to PKR {budget}:\n"
        total_ratings = 0
        total_price = 0
        count = 0

        for product in query_result:
            # Create a Daraz search link
            daraz_link = f"https://www.daraz.pk/catalog/?q={'+'.join(product['Title'].split())}&_keyori=ss&from=input&spm=a2a0e.home.search.go.35e3407617mRpH"

            response += f"<br>Title: <a href='{daraz_link}' target='_blank'>{product['Title']}</a><br>"
            response += f"Price: PKR {product['Price']:.2f}<br>Ratings: {product['MinRatings']}<br>Total Reviews: {product['TotalReviews']}<br>"

            # Check for None values before performing addition
            if product['Price'] is not None:
                count += 1
                total_price += product['Price']

            total_ratings += product['MinRatings']

            # Retrieve reviews for the current product
            review_query = "SELECT * FROM product_reviews WHERE Title = %s"
            review_query_result = execute_query(review_query, connection, (product['Title'],))
            # if review_query_result:
            #     response += f"Total Reviews: {len(review_query_result)}<br>"
        else:
                response += "No reviews found.<br>"

        # Calculate average ratings and price only if there are non-None values
        if count > 0:
            average_ratings = total_ratings / len(query_result)
            average_price = total_price / count
            response += f"<br>Average Price: PKR {average_price:.2f}<br>"
            response += f"Average Rating: {average_ratings:.2f}<br>"

        return response
    else:
        return f"No smartphones found for {brand} within the specified budget range."


def process_generic_query(user_query, connection):
    budget_match = re.search(r'(under|below) (\$?[\d,]+)', user_query)
    if budget_match:
        budget_str = budget_match.group(2).replace(',', '')
        try:
            budget = float(budget_str)
        except ValueError:
            return "I couldn't understand the budget. Please provide a valid budget."

        if not (19499 <= budget <= 267000):
            return "Please provide a budget within the valid range of $19499 to $267000."

        return execute_generic_query(connection, budget)
    else:
        return "I'm not sure how to respond to that. If you have a specific question or request, feel free to let me know!"


def execute_generic_query(connection, budget):
    query = f"""
            SELECT 
                pd.Title, 
                MIN(pd.Price) as Price,
                IFNULL(MIN(pd.Ratings), 0) as MinRatings,
                COUNT(DISTINCT pr.Review_text) as TotalReviews
            FROM 
                product_details pd
            LEFT JOIN 
                product_reviews pr ON pd.Title = pr.Title
            WHERE 
                pd.Price <= {budget} AND pd.Price >= {budget - 6500}
            GROUP BY 
                pd.Title, pd.Price
            ORDER BY 
                TotalReviews DESC
            LIMIT 3
        """
    query_result = execute_query(query, connection)
    
    total_price = 0
    total_rating = 0
    total_products = 0

    response = []
    if query_result:
        response.append("Based on user ratings and price, the best phones under PKR {0} are:<br>".format(budget))
        for product in query_result:
            # Create a Daraz search link
            daraz_link = f"https://www.daraz.pk/catalog/?q={'+'.join(product['Title'].split())}&_keyori=ss&from=input&spm=a2a0e.home.search.go.35e3407617mRpH"

            response.append("<div class='product-info'>")
            response.append("<p><a href='{0}' target='_blank'>{1}</a></p>".format(daraz_link, product['Title']))
            response.append("<p>Price: PKR {0:.2f}</p>".format(product['Price']))
            response.append("<p>Ratings: {0}</p>".format(product['MinRatings'] if product['MinRatings'] is not None else 'No Rating'))
            response.append("<p>Total Reviews: {0}</p>".format(product['TotalReviews']))
            response.append("</div><br>")

            # Accumulate values for average calculation
            total_price += product['Price']
            total_rating += product['MinRatings'] if product['MinRatings'] is not None else 0
            total_products += 1
    
    # Calculate averages
    average_price = total_price / total_products if total_products > 0 else 0
    average_rating = total_rating / total_products if total_products > 0 else 0

    # Display averages at the end
    response.append("<br>Average Price of All Products: PKR {:.2f}<br>".format(average_price))
    response.append("Average Rating of All Products: {:.2f}<br>".format(average_rating))

    return "".join(response)



# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']

    # Connect to the MySQL database
    connection = connect_to_database()

    if connection:
        # Check the type of query and call the corresponding function
        if "hey" in user_input.lower() or "hello" in user_input.lower():
            response = "Hello! How can I assist you today?"
        elif "brand" in user_input.lower() and "upto" in user_input.lower():
            response = process_brand_budget_query(user_input, connection)
        elif "hey how are you" in user_input.lower():
            response="I am a fine thankyou by the way I am a chatbot and I am here for your assistance feel free to search for your next smartphone!"
        elif "thanks" in user_input.lower() or "thank you" in user_input.lower():
            response = "You're welcome! If you have any more questions, feel free to ask."
        elif "bye" in user_input.lower() or "goodbye" in user_input.lower():
            response = "Goodbye! If you need assistance later, feel free to return."
        elif "under" in user_input.lower() or "below" in user_input.lower():
            response = process_generic_query(user_input, connection)
        elif "over" in user_input.lower() or "above" in user_input.lower():
            response = process_above_query(user_input, connection)
        elif "with" in user_input.lower():
            response = process_specification_query(user_input, connection)
        elif "between" in user_input.lower():
            response = process_range_query(user_input, connection)
        elif "less than" in user_input.lower() and "rating greater than" in user_input.lower():
            response = process_condition_query(user_input, connection)
        elif "company" in user_input.lower():
            response = process_company_mobiles_query(user_input, connection)
        else:
            response = "I'm not sure how to respond to that. If you have a specific question or request, feel free to let me know!"

        # Disconnect from the database when done
        disconnect_from_database(connection)

        # Generate and return the bot's response
        return render_template('index.html', user_input=user_input, bot_response=response)

if __name__ == "__main__":
    app.run(debug=True)
