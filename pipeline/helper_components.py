"""Helper components."""

from typing import NamedTuple

def prepoc_split_dataset(root_path: str
)-> NamedTuple('Outputs', [('training_file_path', str), ('validation_file_path', str),
                            ('testing_file_path', str)]):

  import pandas as pd
  from sklearn import preprocessing
  import os

  os.system('curl -o iris.txt  https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data')
    
    
  columns = ['sepal_length','sepal_width','petal_length','petal_width','class']

  dfIris = pd.read_csv('iris.data', names=columns)
  le = preprocessing.LabelEncoder()
  dfIris['classEncoder'] = le.fit_transform(dfIris['class'])
    
  X_train, X_val_test, y_train, y_val_test = train_test_split(dfIris.drop(['classEncoder','class'], axis=1),     dfIris['classEncoder'], test_size=0.2)

  X_val, X_test, y_val, y_test = train_test_split(X_val_test,y_val_test, test_size=0.5)
    
  df_train = pd.concat([X_train,y_train],axis=1)
  df_val = pd.concat([X_val,y_val],axis=1)
  df_test = pd.concat([X_test,y_test],axis=1)
  
  training_file_path = '{}/train.txt'.format(training_file_path)
  validation_file_path = '{}/validation.txt'.format(validation_file_path
  testing_file_path  = '{}/test.txt'.format(testing_file_path)                                                
  
  df_train.to_csv(training_file_path, index=False)
  df_val.to_csv(validation_file_path, index=False)
  df_test.to_csv(testing_file_path , index=False)
  
  return (training_file_path,validation_file_path,testing_file_path)

def retrieve_best_run(
    project_id: str, job_id: str
) -> NamedTuple('Outputs', [('metric_value', float), ('alpha', float),
                            ('max_iter', int)]):
  """Retrieves the parameters of the best Hypertune run."""

  from googleapiclient import discovery
  from googleapiclient import errors

  ml = discovery.build('ml', 'v1')

  job_name = 'projects/{}/jobs/{}'.format(project_id, job_id)
  request = ml.projects().jobs().get(name=job_name)

  try:
    response = request.execute()
  except errors.HttpError as err:
    print(err)
  except:
    print('Unexpected error')

  print(response)

  best_trial = response['trainingOutput']['trials'][0]

  metric_value = best_trial['finalMetric']['objectiveValue']
  alpha = float(best_trial['hyperparameters']['alpha'])
  max_iter = int(best_trial['hyperparameters']['max_iter'])

  return (metric_value, alpha, max_iter)


def evaluate_model(
    dataset_path: str, model_path: str, metric_name: str
) -> NamedTuple('Outputs', [('metric_name', str), ('metric_value', float),
                            ('mlpipeline_metrics', 'Metrics')]):
  """Evaluates a trained sklearn model."""
  #import joblib
  import pickle
  import json
  import pandas as pd
  import subprocess
  import sys

  from sklearn.metrics import accuracy_score, recall_score

  df_test = pd.read_csv(dataset_path)

  X_test = df_test.drop('Cover_Type', axis=1)
  y_test = df_test['Cover_Type']

  # Copy the model from GCS
  model_filename = 'model.pkl'
  gcs_model_filepath = '{}/{}'.format(model_path, model_filename)
  print(gcs_model_filepath)
  subprocess.check_call(['gsutil', 'cp', gcs_model_filepath, model_filename],
                        stderr=sys.stdout)

  with open(model_filename, 'rb') as model_file:
    model = pickle.load(model_file)

  y_hat = model.predict(X_test)

  if metric_name == 'accuracy':
    metric_value = accuracy_score(y_test, y_hat)
  elif metric_name == 'recall':
    metric_value = recall_score(y_test, y_hat)
  else:
    metric_name = 'N/A'
    metric_value = 0

  # Export the metric
  metrics = {
      'metrics': [{
          'name': metric_name,
          'numberValue': float(metric_value)
      }]
  }

  return (metric_name, metric_value, json.dumps(metrics))