import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import fastf1
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

# Get feature importances
feature_importances = pd.Series(gb_model.feature_importances_, index=X.columns)

# Sort feature importances in descending order
sorted_feature_importances = feature_importances.sort_values(ascending=False)

# Plot the feature importances
plt.figure(figsize=(14, 8))
sorted_feature_importances.plot(kind='bar')
plt.title('Gradient Boosting Feature Importance for Lap Time Prediction')
plt.xlabel('Features')
plt.ylabel('Importance')
plt.show()
