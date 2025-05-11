# How to Run

### 1. Install the required dependencies

#### Install the required dependencies by running the following command in your terminal:

```
 pip install -r requirements.txt
 ```

### 2. Create a .env file

#### Create a .env file in the root directory of the project and add the following environment variables:

```
 DB_USER=your_postgres_user
 DB_PASSWORD=your_postgres_password
 DB_NAME=llm_engineering_tool
 ```

### Note:

#### Make sure to replace `your_postgres_user` and

`your_postgres_password` with your actual PostgreSQL database credentials.

#### Make sure to create a database named `llm_engineering_tool` in your PostgreSQL server.

### 3. Run the application

#### Run the application by executing the following command in your terminal:

```
 uvicorn main:app --reload
 ```
