import tensorflow as tf
from model.utils import compose

class Conv2D_BN_LeakyRelu(tf.keras.layers.Layer):
    def __init__(self, num_filter, kernel_size, down_sample=False):
        super(Conv2D_BN_LeakyRelu, self).__init__(name='')
        if down_sample:
            stride = (2, 2)
            padding = 'valid'
        else:
            stride = (1, 1)
            padding = 'same'
        kernel_size = (kernel_size, kernel_size)
        self.conv = tf.keras.layers.Conv2D(num_filter, kernel_size, stride, padding)
        self.bn = tf.keras.layers.BatchNormalization()
        self.leaky = tf.keras.layers.LeakyReLU(alpha=0.1)

    def call(self, input_tensor, training=False):
        x = self.conv(input_tensor)
        x = self.bn(x)
        x = self.leaky(x)
        return x

def getResnetBlock(inputs, num_filter, num_repeat, training=False):
    x = tf.keras.layers.ZeroPadding2D(((1,0),(1,0)))(inputs)
    x = Conv2D_BN_LeakyRelu(num_filter, 3, down_sample=True)(x, training=training)
    for i in range(num_repeat):
        tmp_x = x
        x = Conv2D_BN_LeakyRelu(num_filter//2, 1, down_sample=False)(x, training=training)
        x = Conv2D_BN_LeakyRelu(num_filter, 3, down_sample=False)(x, training=training)
        x = tf.keras.layers.Add()([x, tmp_x])
    return x

def getDarkNet53(inputs, training=False):
    x = Conv2D_BN_LeakyRelu(32, 3, down_sample=False)(inputs)
    x = getResnetBlock(x, 64, 1, training=training)
    x = getResnetBlock(x, 128, 2, training=training)
    x = getResnetBlock(x, 256, 8, training=training)
    out_1 = x
    x = getResnetBlock(x, 512, 8, training=training)
    out_2 = x
    x = getResnetBlock(x, 1024, 4, training=training)
    return out_1, out_2, x

def get6Layers(inputs, num_filters, out_filters):
    x = Conv2D_BN_LeakyRelu(num_filters, 1, down_sample=False)(inputs)
    x = Conv2D_BN_LeakyRelu(num_filters*2, 3, down_sample=False)(x)
    x = Conv2D_BN_LeakyRelu(num_filters, 1, down_sample=False)(x)
    x = Conv2D_BN_LeakyRelu(num_filters*2, 3, down_sample=False)(x)
    x = Conv2D_BN_LeakyRelu(num_filters, 1, down_sample=False)(x)
    out_1 = x
    x = Conv2D_BN_LeakyRelu(num_filters*2, 3, down_sample=False)(x)
    x = Conv2D_BN_LeakyRelu(out_filters, 1, down_sample=False)(x)
    return out_1, x

def getYoloV3(inputs, num_anchors, num_classes):
    out_1, out_2, out_3 = getDarkNet53(inputs)

    x, y1 = get6Layers(out_3, 512, num_anchors*(num_classes+5))
    x = Conv2D_BN_LeakyRelu(256, 1, down_sample=False)(x)
    x = tf.keras.layers.UpSampling2D(2)(x)
    x = tf.keras.layers.concatenate([x, out_2])

    x, y2 = get6Layers(x, 256, num_anchors*(num_classes+5))
    x = Conv2D_BN_LeakyRelu(128, 1, down_sample=False)(x)
    x = tf.keras.layers.UpSampling2D(2)(x)
    x = tf.keras.layers.concatenate([x, out_1])

    x, y3 = get6Layers(x, 128, num_anchors*(num_classes+5))
    
    return y1, y2, y3