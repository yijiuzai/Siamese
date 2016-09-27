import numpy as np
from keras.optimizers import SGD, RMSprop
from keras.layers import Input, Lambda, Dense, Dropout
from keras.models import Model
from keras.callbacks import EarlyStopping

from matplotlib import pyplot as plt
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.cross_validation import train_test_split

import createFaceData
from SiameseFunctions import create_base_network, eucl_dist_output_shape, euclidean_distance, contrastive_loss, compute_accuracy


# get the data
samp_f = 3
total_to_samp = 30000
x, y = createFaceData.gen_data_new(samp_f, total_to_samp)
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=.25)
# x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=.30)


# because we re-use the same instance `base_network`,
# the weights of the network
# will be shared across the two branches
input_dim = x_train.shape[2]
input_a = Input(shape=(input_dim,))
input_b = Input(shape=(input_dim,))
hidden_layer_sizes = [128, 128, 128]
base_network = create_base_network(input_dim, hidden_layer_sizes)
processed_a = base_network(input_a)
processed_b = base_network(input_b)

distance = Lambda(euclidean_distance, output_shape=eucl_dist_output_shape)([processed_a, processed_b])

model = Model(input=[input_a, input_b], output=distance)

# train
nb_epoch = 10
rms = RMSprop()
model.compile(loss=contrastive_loss, optimizer=rms)
model.fit([x_train[:, 0], x_train[:, 1]], y_train, validation_split=.25,
          batch_size=128, verbose=2, nb_epoch=nb_epoch)

# compute final accuracy on training and test sets
pred_tr = model.predict([x_train[:, 0], x_train[:, 1]])
tr_acc = compute_accuracy(pred_tr, y_train)
pred_ts = model.predict([x_test[:, 0], x_test[:, 1]])
te_acc = compute_accuracy(pred_ts, y_test)

print('* Accuracy on training set: %0.2f%%' % (100 * tr_acc))
print('* Accuracy on test set: %0.2f%%' % (100 * te_acc))
print('* Mean of error less than .5 (match): %0.3f%%' % np.mean(pred_ts[pred_ts < .5]))
print('* Mean of error more than .5 (no match): %0.3f%%' % np.mean(pred_ts[pred_ts >= .5]))
print("* test case confusion matrix:")
print(confusion_matrix((pred_ts <= .5).astype('float32'), y_test))
plt.hold(False)
plt.plot(np.concatenate([pred_ts[pred_ts < .5], pred_ts[pred_ts >= .5]]))
plt.savefig('pair_errors.png')
