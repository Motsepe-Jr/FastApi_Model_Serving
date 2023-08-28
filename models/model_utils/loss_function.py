import tensorflow as tf

def lat_lon_loss(y_true, y_pred):
    lat_true, lon_true = y_true[:, 0], y_true[:, 1]
    lat_pred, lon_pred = y_pred[:, 0], y_pred[:, 1]
    loss_lat = tf.keras.losses.mean_squared_error(lat_true, lat_pred)
    loss_lon = tf.keras.losses.mean_squared_error(lon_true, lon_pred)
    return loss_lat + loss_lon