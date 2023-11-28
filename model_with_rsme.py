import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import LabelEncoder

# Assuming you have a DataFrame 'df' with your lap time data
selected_gp_session = fastf1.get_session(2023, "Spanish Grand Prix", "Race")
selected_gp_session.load()
df = selected_gp_session.laps

# Convert LapTime to seconds
df['LapTime_seconds'] = df['LapTime'].dt.total_seconds()

# Example: Features (X) and Target (y)
feature_columns = ['DriverNumber', 'LapNumber', 'Stint',
                    'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST', 
                    'Compound', 'TyreLife', 'FreshTyre', 'TrackStatus']

X = df[feature_columns].copy()  # Create a copy of the DataFrame
y = df['LapTime_seconds']  # Use the converted LapTime column

# Label encode categorical columns
le = LabelEncoder()
X['Compound'] = le.fit_transform(X['Compound'])

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Impute missing values in features
imputer = SimpleImputer(strategy='mean')
X_train_imputed = pd.DataFrame(imputer.fit_transform(X_train), columns=X_train.columns)

# Impute missing values in target variable
imputer_y = SimpleImputer(strategy='mean')
y_train_imputed = imputer_y.fit_transform(y_train.values.reshape(-1, 1))

# Initialize the Gradient Boosting Regressor
gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)

# Fit the model to the training data with imputed values
gb_model.fit(X_train_imputed, y_train_imputed.ravel())

# Get predictions on the test set
X_test_imputed = pd.DataFrame(imputer.transform(X_test), columns=X_test.columns)
y_pred = gb_model.predict(X_test_imputed)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
print(f'Mean Squared Error on Test Set: {mse}')

# You can also use the model to predict lap times for new data
# new_data = pd.DataFrame(...)  # Create a DataFrame with the same columns as your training data
# new_data_imputed = pd.DataFrame(imputer.transform(new_data), columns=new_data.columns)
# new_predictions = gb_model.predict(new_data_imputed)
