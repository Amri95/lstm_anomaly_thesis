import models.lstm as lstm
import configuration.config as cfg
import matplotlib

if cfg.run_config['Xserver'] == False:
    print "No X-server"
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
import time

if cfg.run_config['Xserver']:
    from keras.utils import plot_model
import utilities.utils as util
import numpy as np
import logging
from keras.callbacks import EarlyStopping

# import plotly
# import plotly.plotly as py
# import plotly.graph_objs as go
# plotly.tools.set_credentials_file(username='aakashsingh', api_key='iMfR7hS1dbnmJ9XB17XO')

np.random.seed(123)


def make_plots(context,predictions_timesteps,true_values,look_ahead,title,path,save_figure,Xserver):
    step = 1
    if look_ahead > 1:
        step = look_ahead - 1
    for idx, i in enumerate(np.arange(0, look_ahead, step)):
        plt.figure()
        plt.title(title+" Timestep: %d "%i)
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.plot(true_values, label="actual", linewidth=1)
        plt.plot(predictions_timesteps[:, i], label="prediction", linewidth=1, linestyle="--")
        error = abs(true_values - predictions_timesteps[:, i])
        plt.plot(error, label="error", linewidth=0.5)
        plt.legend()
        plt.tight_layout()
        if save_figure:
            util.save_figure(path,"%s_timestep_%d"%(context,i), plt)

    if Xserver:
        plt.show()

    # print "Plotting Validation results"
    # x_data = np.arange(0, len(y_validation2_true))
    # # trace_true = go.Scatter(
    # #     x= x_data,
    # #     y= testY_1,
    # #     name = "actual"
    # # )
    #
    # step = 1
    # if look_ahead > 1:
    #     step = look_ahead - 1
    # for idx, i in enumerate(np.arange(0, look_ahead, step)):
    #     plt.figure()
    #     plt.title(
    #         "Prediction on validation2 data for t+%d timestep.  %d epochs, look back %d, look_ahead %d & batch_size %d" % (
    #         i + 1, epochs, look_back, look_ahead, batch_size))
    #     plt.plot(y_validation2_true, label="actual", linewidth=1)
    #     plt.plot(validation2_predictions_timesteps[:, i], label="prediction", linewidth=1)
    #     error = abs(y_validation2_true - validation2_predictions_timesteps[:, i])
    #     plt.plot(error, label="error", linewidth=0.5)
    #     plt.legend()
    #     plt.xlabel("Time")
    #     plt.ylabel("Value")
    #     plt.tight_layout()
    #     if cfg.run_config['save_figure']:
    #         util.save_figure("imgs/" + experiment_id, "validation_timestep_%d.png" % (i + 1), plt)
    #
    #         # trace_predicted = go.Scatter(
    #         #     x=x_data,
    #         #     y=test_diagonals[:, i],
    #         #     name="predicted_t+%d" % (i + 1)
    #         # )
    #         # trace_error = go.Scatter(
    #         #     x=x_data,
    #         #     y=error,
    #         #     name="error_t+%d" % (i + 1)
    #         # )
    #         # plotly_data = [trace_true,trace_predicted,trace_error]
    #         # py.plot(plotly_data, filename='lstm_timestep_%d'%(i+1))
    #
    # if cfg.run_config['Xserver']:
    #     plt.show()


def get_predictions(context,model,X,y,train_scaler,batch_size,look_ahead,look_back,epochs,experiment_id):
    predictions = model.predict(X, batch_size=batch_size)
    print predictions.shape
    # rescale
    predictions = train_scaler.inverse_transform(predictions)
    y = train_scaler.inverse_transform(y)

    # extract first timestep for true values
    y_true = y[:, 0].flatten()

    # diagonals contains a reading's values calculated at different points in time
    diagonals = util.get_diagonals(predictions)

    # the top left and bottom right predictions do not contain predictions for all timesteps
    # fill the missing prediction values in diagonals. curenttly using the first predicted value for all missing timesteps
    for idx, diagonal in enumerate(diagonals):
        diagonal = diagonal.flatten()
        # missing value filled with the first value
        diagonals[idx] = np.hstack((diagonal, np.full(look_ahead - len(diagonal), diagonal[0])))
    predictions_timesteps = np.asarray(diagonals)

    for i in range(look_ahead):
        logging.info("%s RMSE on %d timestep prediction %f" % ( context,
            (i + 1), mean_squared_error(y_true, predictions_timesteps[:, i]) ** 0.5))

    shifted_1 = util.shift_time_series(y_true, 1)

    logging.info(" %s RMSE Naive One Timestep Shift %f",context,
                 mean_squared_error(y_true[1:], shifted_1[1:]) ** 0.5)

    title = "Prediction on %s data. %d epochs, look back %d, look_ahead %d & batch_size %d." % (
                 context, epochs, look_back, look_ahead, batch_size)
    path = "%s/%s/"%("imgs",experiment_id)
    make_plots(context,predictions_timesteps,y_true,look_ahead,title,path,cfg.run_config['save_figure'],
               cfg.run_config['Xserver'])

    return predictions_timesteps, y_true


# def evaluate_model(model,X_train,y_train,X_validation2,y_validation2,train_scaler,batch_size,look_ahead,look_back,epochs,experiment_id,data_folder):
#     train_predictions = model.predict(X_train, batch_size=batch_size)
#     validation2_predictions = model.predict(X_validation2, batch_size=batch_size)
#     print train_predictions.shape
#     # rescale
#     train_predictions = train_scaler.inverse_transform(train_predictions)
#     y_train = train_scaler.inverse_transform(y_train)
#     validation2_predictions = train_scaler.inverse_transform(validation2_predictions)
#     y_validation2 = train_scaler.inverse_transform(y_validation2)
#
#     # extract first timestep for true values
#     y_train_true = y_train[:, 0].flatten()
#     y_validation2_true = y_validation2[:, 0].flatten()
#
#     # diagonals contains a reading's values calculated at different points in time
#     train_diagonals = util.get_diagonals(train_predictions)
#     validation2_diagonals = util.get_diagonals(validation2_predictions)
#
#     # the top left and bottom right predictions do not contain predictions for all timesteps
#     # fill the missing prediction values in diagonals. curenttly using the first predicted value for all missing timesteps
#     for idx, diag in enumerate(validation2_diagonals):
#         diag = diag.flatten()
#         # missing value filled with the first value
#         validation2_diagonals[idx] = np.hstack((diag, np.full(look_ahead - len(diag), diag[0])))
#     validation2_predictions_timesteps = np.asarray(validation2_diagonals)
#
#     for idx, diag in enumerate(train_diagonals):
#         diag = diag.flatten()
#         # missing value filled with the first value
#         train_diagonals[idx] = np.hstack((diag, np.full(look_ahead - len(diag), diag[0])))
#     train_predictions_timesteps = np.asarray(train_diagonals)
#
#     for i in range(look_ahead):
#         logging.info("Train RMSE on %d timestep prediction %f" % (
#             (i + 1), mean_squared_error(y_train_true, train_predictions_timesteps[:, i]) ** 0.5))
#     for i in range(look_ahead):
#         logging.info("Validation RMSE on %d timestep prediction %f" % (
#             (i + 1), mean_squared_error(y_validation2_true, validation2_predictions_timesteps[:, i]) ** 0.5))
#
#     validation_shifted_1 = util.shift_time_series(y_validation2_true, 1)
#     logging.info("validationY_1,validation_shifted_1")
#     for i in range(3):
#         logging.info("%f,%f" % (y_validation2_true[i], validation_shifted_1[i]))
#     logging.info("RMSE Naive One Timestep Shift %f",
#                  mean_squared_error(y_validation2_true[1:], validation_shifted_1[1:]) ** 0.5)
#
#     title = "Prediction on training data. %d epochs, look back %d, look_ahead %d & batch_size %d." % (
#                  epochs, look_back, look_ahead, batch_size)
#     path = "%s/%s/"%("imgs",experiment_id)
#     make_plots('train',train_predictions_timesteps,y_train_true,look_ahead,title,path,cfg.run_config['save_figure'],
#                cfg.run_config['Xserver'])
#
#     title = "Prediction on validation2 data. %d epochs, look back %d, look_ahead %d & batch_size %d." % (
#                 epochs, look_back, look_ahead, batch_size)
#     path = "%s/%s/" % ("imgs", experiment_id)
#     make_plots('validation2',validation2_predictions_timesteps, y_validation2_true, look_ahead, title, path,
#                cfg.run_config['save_figure'],
#                cfg.run_config['Xserver'])
#     model.sa
#     np.save(data_folder+"train_predictions",train_predictions_timesteps)
#     np.save(data_folder+"y_train_true",y_train_true)
#     np.save(data_folder + "validation2_predictions", validation2_predictions_timesteps)
#     np.save(data_folder + "y_validation_true", y_validation2_true)


def run():
    #load config settings
    experiment_id = cfg.run_config['experiment_id']
    data_folder = cfg.run_config['data_folder']
    look_back = cfg.multi_step_lstm_config['look_back']
    look_ahead = cfg.multi_step_lstm_config['look_ahead']
    batch_size = cfg.multi_step_lstm_config['batch_size']
    epochs = cfg.multi_step_lstm_config['n_epochs']
    train_test_ratio = cfg.multi_step_lstm_config['train_test_ratio']
    dropout = cfg.multi_step_lstm_config['dropout']
    layers = cfg.multi_step_lstm_config['layers']
    loss = cfg.multi_step_lstm_config['loss']
    # optimizer = cfg.multi_step_lstm_config['optimizer']
    shuffle = cfg.multi_step_lstm_config['shuffle']
    patience = cfg.multi_step_lstm_config['patience']
    validation = cfg.multi_step_lstm_config['validation']
    learning_rate = cfg.multi_step_lstm_config['learning_rate']
    logging.info("----------------------------------------------------")
    logging.info('Run id %s' % (experiment_id))

    logging.info(" HYPERPRAMRAMS : %s" % (str(locals())))

    train_scaler, X_train, y_train, X_validation1, y_validation1, X_validation2, y_validation2, validation2_labels, \
    X_test, y_test, test_labels = util.load_data(data_folder, look_back, look_ahead)



    multistep_lstm = lstm.MultiStepLSTM( look_back=look_back, look_ahead=look_ahead,
                                          layers=layers,
                                          dropout=dropout, loss=loss, learning_rate=learning_rate)
    model = multistep_lstm.build_model()
    if cfg.run_config['Xserver']:
        plot_model(model, to_file="imgs/multistep_lstm.png", show_shapes=True, show_layer_names=True)
    # train model on training set. validation1 set is used for early stopping
    lstm.train_model(model, X_train, y_train, batch_size, epochs, shuffle, validation, (X_validation1, y_validation1), patience)

    validation2_loss = model.evaluate(X_validation2, y_validation2, batch_size=batch_size, verbose=2)
    print "Validation2 Loss %s" % (validation2_loss)
    logging.info("Validation2 Loss %s" % (validation2_loss))
    test_loss = model.evaluate(X_test, y_test, batch_size=batch_size, verbose=2)
    print "Test Loss %s" % (test_loss)
    logging.info("Test Loss %s" % (test_loss))

    predictions_train, y_true_train = get_predictions("Train", model, X_train, y_train, train_scaler,
                                                               batch_size, look_ahead, look_back, epochs, experiment_id,
                                                               )
    np.save(data_folder + "train_predictions", predictions_train)
    np.save(data_folder + "train_true",y_true_train)
    predictions_validation2, y_true_validation2 = get_predictions("Validation2", model, X_validation2, y_validation2,
                                                                  train_scaler, batch_size, look_ahead, look_back,
                                                                  epochs, experiment_id,
                                                                 )
    predictions_validation2_scaled = train_scaler.transform(predictions_validation2)
    print "Calculated validation2 loss %f"%(mean_squared_error(
        np.reshape(y_validation2, [len(y_validation2), look_ahead]),
        np.reshape(predictions_validation2_scaled, [len(predictions_validation2_scaled), look_ahead])))

    np.save(data_folder + "validation2_predictions", predictions_validation2)
    np.save(data_folder + "validation2_true", y_true_validation2)
    np.save(data_folder + "validation2_labels", validation2_labels)
    predictions_test, y_true_test = get_predictions("Test", model, X_test, y_test, train_scaler, batch_size, look_ahead,
                                                    look_back, epochs, experiment_id,
                                                   )
    predictions_test_scaled = train_scaler.transform(predictions_test)
    print "Calculated test loss %f" % (mean_squared_error( np.reshape(y_test, [len(y_test),look_ahead]),
                                       np.reshape(predictions_test_scaled, [len(predictions_test_scaled),look_ahead])))

    np.save(data_folder + "test_predictions", predictions_test)
    np.save(data_folder + "test_true", y_true_test)
    np.save(data_folder + "test_labels", test_labels)
    logging.info("-------------------------run complete----------------------------------------------")


if __name__ == "__main__":
    # load config params
    FORMAT = '%(asctime)-15s. %(message)s'
    logger = logging.basicConfig(filename=cfg.run_config['log_file'], level=logging.INFO, format=FORMAT)
    run()
    logging.info("")
