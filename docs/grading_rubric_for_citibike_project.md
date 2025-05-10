Final Project
Citi Bike Trip Prediction System
Overview
In this project, you will design and implement a Citi Bike trip prediction system using publicly available Citi Bike trip history data. This assignment is a direct adaptation of Project #1, which focused on predicting hourly NYC taxi rides, but here you will use Citi Bike ride data as your source. You are expected to independently plan and execute the entire pipeline, including data engineering, modeling, automation, deployment, and frontend/monitoring. While you may reference code and concepts from previous projects, all work must be your own.

Data Source: Citi Bike System Data
Due Date: March 10, 2025
TA Review Call: You must schedule a 15-minute review call with the TA on May 10–11, 2025, to demonstrate your work.

Note: Exceptional performance on this project can outweigh your first two projects and significantly improve your final grade. The TA’s subjective assessment, worth 10% of your grade, can tip the balance in your favor if you demonstrate outstanding work, insight, or initiative.

Project Requirements
Project Presentation
Prepare a comprehensive PowerPoint presentation that includes:

A detailed explanation of your data engineering workflow (fetching, cleaning, and storing data in Hopsworks)
Your implementation plan for the feature engineering pipeline
Your implementation plan for the inference pipeline
Your implementation plan for the model training pipeline
A clear explanation of how batch prediction will work in your system
Diagrams or flowcharts illustrating these processes (highly recommended)
Data Engineering
Fetch raw Citi Bike trip data from https://citibikenyc.com/system-data
Select top 3 locations 
Clean and preprocess the data
Store the transformed data in Hopsworks
Modeling & Experiment Tracking
Develop and log at least three models in MLflow:
A baseline model (e.g., simple mean or naive lag)
A model using all lag features for the past 28 days (e.g., LightGBM with 28 lag features)
A model with feature reduction (e.g., top 10 features selected using feature importance or PCA)
For each model, log the MAE and demonstrate improvements over the baseline
Use an appropriate train/test split methodology
Store all model runs and metrics in MLflow
Automation & Deployment
Implement three working GitHub Actions (for feature engineering, inference, and model training)
Load time series data, the best model, and inference/predictions into Hopsworks
Deploy models to Hopsworks
Frontend & Monitoring
Build a publicly accessible and fully functional prediction app using Streamlit
Build a publicly accessible and fully functional model monitoring app
Project Structure & Subjective Assessment
Maintain a well-organized GitHub repository (including notebooks, source code, pipelines, and frontend)
Schedule and attend a 15-minute review call with the TA on May 10–11, 2025
Be prepared to explain and demonstrate all parts of your project
The TA will evaluate your understanding, initiative, and overall project quality during the review call
This subjective assessment is worth 20% of your grade and can positively influence your final mark if you demonstrate good understanding and functioning pipelines and streamlit app.
Grading Rubric
Category Points (%)
Data Engineering 25
Modeling & Experiment Tracking 20
Automation & Deployment 20
Frontend & Monitoring 15
Project Structure & Subjective Assessment 20
Total 100
Note:
This project is a direct adaptation of Project #1 (NYC hourly taxi ride prediction), with the primary change being the use of Citi Bike ride data instead of taxi data. You are encouraged to use online resources and AI tools to assist with the project. Collaboration is allowed, but you must maintain your own working copy and be able to explain every part of your submission.
