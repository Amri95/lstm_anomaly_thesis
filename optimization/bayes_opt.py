import GPyOpt
from numpy.random import seed
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import models.lstm as lstm
import utilities.utils as util
import configuration.config as cfg
import logging
import traceback
from keras.callbacks import EarlyStopping
import numpy as np

FORMAT = '%(asctime)-15s. %(message)s'
logger = logging.basicConfig(filename=cfg.opt_config['log_file'], level=logging.INFO, format=FORMAT)

seed(123)
validation_loss_list = []


def stateful_objective_function(params):
    params = params.flatten()
    logging.info("----------------------------------------------------")
    logging.info("inside objective function. params received: %s" % params)
    #optimizers = ['sgd', 'adam', 'rmsprop']
    layers_array = [{'input': 1, 'hidden1': 64, 'output': 1},
                    {'input': 1, 'hidden1': 60, 'hidden2': 30, 'output': 1},
                    {'input': 1, 'hidden1': 60, 'hidden2': 30, 'hidden3': 10, 'output': 1}
                    ]

    dropout = float(params[0])
    learning_rate = float(params[1])
    look_back = int(params[2])
    layers = layers_array[int(params[3])]
    batch_size = look_back

    print("Using HyperParams. dropout:%f, learning_rate:%f, batch_size:%d, lookback:%d, layers:%s" % (dropout, learning_rate, batch_size, look_back,layers))
    logging.info("Using HyperParams. dropout:%f, learning_rate:%f, batch_size:%d, lookback:%d, layers:%s" % (dropout, learning_rate, batch_size,look_back, layers))
    data_folder = cfg.opt_config['data_folder']
    look_ahead = cfg.multi_step_lstm_config['look_ahead']
    epochs = cfg.multi_step_lstm_config['n_epochs']
    train_test_ratio = cfg.multi_step_lstm_config['train_test_ratio']
    #layers = cfg.multi_step_lstm_config['layers']
    loss = cfg.multi_step_lstm_config['loss']
    shuffle = cfg.multi_step_lstm_config['shuffle']
    patience = cfg.multi_step_lstm_config['patience']
    validation = cfg.multi_step_lstm_config['validation']
    logging.info('Optimizing id %s' % (opt_id))
    train_scaler, X_train, y_train, X_validation1, y_validation1, X_validation2, y_validation2, validation2_labels, \
    X_test, y_test, test_labels = util.load_data(data_folder, look_back, look_ahead)

    # For stateful lstm the batch_size needs to be fixed before hand.
    # We also need to ernsure that all batches shud have the same number of samples. So we drop the last batch as it has less elements than batch size
    if batch_size > 1:
        n_train_batches = len(X_train) / batch_size
        len_train = n_train_batches * batch_size
        if len_train < len(X_train):
            X_train = X_train[:len_train]
            y_train = y_train[:len_train]

        n_validation1_batches = len(X_validation1) / batch_size
        len_validation1 = n_validation1_batches * batch_size
        if n_validation1_batches * batch_size < len(X_validation1):
            X_validation1 = X_validation1[:len_validation1]
            y_validation1 = y_validation1[:len_validation1]

        n_validation2_batches = len(X_validation2) / batch_size
        len_validation2 = n_validation2_batches * batch_size
        if n_validation2_batches * batch_size < len(X_validation2):
            X_validation2 = X_validation2[:len_validation2]
            y_validation2 = y_validation2[:len_validation2]

        n_test_batches = len(X_test) / batch_size
        len_test = n_test_batches * batch_size
        if n_test_batches * batch_size < len(X_test):
            X_test = X_test[:len_test]
            y_test = y_test[:len_test]

    stateful_lstm = lstm.StatefulMultiStepLSTM(batch_size=batch_size, look_back=look_back, look_ahead=look_ahead,
                                               layers=layers,
                                               dropout=dropout, loss=loss, learning_rate=learning_rate)
    model = stateful_lstm.build_model()
    # train model on training set. validation1 set is used for early stopping
    lstm.train_model(model, X_train, y_train, batch_size, epochs, shuffle, validation, (X_validation1, y_validation1),
                     patience)

    validation2_loss = model.evaluate(X_validation2, y_validation2, batch_size=batch_size, verbose=2)
    logging.info("validation2 loss %f"%(validation2_loss))
    print(" ")
    print(" #######validation2 loss %f#########" % (validation2_loss))
    validation_loss_list.append(validation2_loss)
    return validation2_loss


def multistep_objective_function(params):
    params = params.flatten()
    logging.info("----------------------------------------------------")
    logging.info("inside objective function. params received: %s" % params)
    #optimizers = ['sgd', 'adam', 'rmsprop']
    layers_array = [{'input': 1, 'hidden1': 64, 'output': 1},
                    {'input': 1, 'hidden1': 60, 'hidden2': 30, 'output': 1},
                    {'input': 1, 'hidden1': 60, 'hidden2': 30, 'hidden3': 10, 'output': 1}
                    ]

    dropout = float(params[0])
    learning_rate = float(params[1])
    batch_size = int(params[2])
    look_back = int(params[3])
    layers = layers_array[int(params[4])]


    print("Using HyperParams. dropout:%f, learning_rate:%f, batch_size:%d, lookback:%d, layers:%s" % (dropout, learning_rate, batch_size, look_back,layers))
    logging.info("Using HyperParams. dropout:%f, learning_rate:%f, batch_size:%d, lookback:%d, layers:%s" % (dropout, learning_rate, batch_size,look_back, layers))
    data_folder = cfg.opt_config['data_folder']
    look_ahead = cfg.multi_step_lstm_config['look_ahead']
    epochs = cfg.multi_step_lstm_config['n_epochs']
    train_test_ratio = cfg.multi_step_lstm_config['train_test_ratio']
    #layers = cfg.multi_step_lstm_config['layers']
    loss = cfg.multi_step_lstm_config['loss']
    shuffle = cfg.multi_step_lstm_config['shuffle']
    patience = cfg.multi_step_lstm_config['patience']
    validation = cfg.multi_step_lstm_config['validation']
    logging.info('Optimizing id %s' % (opt_id))
    train_scaler, X_train, y_train, X_validation1, y_validation1, X_validation2, y_validation2, validation2_labels, \
    X_test, y_test, test_labels = util.load_data(data_folder, look_back, look_ahead)

    multistep_lstm = lstm.MultiStepLSTM(look_back=look_back, look_ahead=look_ahead,
                                               layers=layers,
                                               dropout=dropout, loss=loss, learning_rate=learning_rate)
    model = multistep_lstm.build_model()
    # train model on training set. validation1 set is used for early stopping
    lstm.train_model(model, X_train, y_train, batch_size, epochs, shuffle, validation, (X_validation1, y_validation1),
                     patience)

    validation2_loss = model.evaluate(X_validation2, y_validation2, batch_size=batch_size, verbose=2)
    logging.info("validation2 loss %f"%(validation2_loss))
    print(" ")
    print(" #######validation2 loss %f#########" % (validation2_loss))
    validation_loss_list.append(validation2_loss)
    return validation2_loss


multistep_domain =[{'name': 'dropout', 'type': 'continuous', 'domain': (0.2,0.7)},
               {'name': 'learning_rate', 'type': 'continuous', 'domain': (0.001, .1)},
               {'name': 'batch_size', 'type': 'discrete', 'domain': (32,64,128,256,512)},
               {'name': 'look_back', 'type': 'discrete', 'domain': (1,3,6,12,24,36,48,64)},
               {'name': 'layers', 'type':'discrete', 'domain':(0,1,2)}
               ]

stateful_domain =[{'name': 'dropout', 'type': 'continuous', 'domain': (0.2,0.7)},
               {'name': 'learning_rate', 'type': 'continuous', 'domain': (0.001, .1)},
               {'name': 'look_back', 'type': 'discrete', 'domain': (1,3,6,12,24,36,48,64)},
               {'name': 'layers', 'type':'discrete', 'domain':(0,1,2)}
               ]

try:
    opt_id = cfg.opt_config['opt_run_id']
    model_type = cfg.opt_config['model']
    max_iter = int(cfg.opt_config['max_iter'])
    initial_evals = int(cfg.opt_config['initial_evals'])

    lstm_bopt = GPyOpt.methods.BayesianOptimization(multistep_objective_function,  # function to optimize
                                                 domain=multistep_domain,  # box-constrains of the problem
                                                 initial_design_numdata = initial_evals,  # number data initial design
                                                 acquisition_type='EI',  # Expected Improvement
                                                 exact_feval = True)         # True evaluations

    # lstm_bopt = GPyOpt.methods.BayesianOptimization(stateful_objective_function,  # function to optimize
    #                                                  domain=stateful_domain,  # box-constrains of the problem
    #                                                  initial_design_numdata=3,  # number data initial design
    #                                                  acquisition_type='EI',  # Expected Improvement
    #                                                  exact_feval=True)  # True evaluations


    #max_time = 300'
    logging.info("================= Start Optimizing=====================")
    lstm_bopt.run_optimization(max_iter)
    logging.info("==Optimization Hyperparams List==")
    logging.info(lstm_bopt.X)
    logging.info("==Optimum Hyperparams==")
    logging.info(lstm_bopt.x_opt)
    logging.info("Min validation loss %f"%min(validation_loss_list))

    for i in range(0,len(validation_loss_list)):
        print "params: %s  loss: %s"%(lstm_bopt.X[i],validation_loss_list[i])
    print("==Optimum Hyperparams==")
    print (lstm_bopt.x_opt)
    print("Min test loss %f" % min(validation_loss_list))
    path = "imgs/%s/"%(opt_id)
    util.mkdir_p(path)
    lstm_bopt.plot_convergence(filename="%s/convergence.png"%(path))
    logging.info("=================End Optimizing=====================")
except:
    traceback.print_exc()
    logging.exception('')
    raise
