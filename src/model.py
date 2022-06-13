import os
from tabnanny import verbose
import tensorflow as tf
from transformers import GPT2Config, TFGPT2LMHeadModel, GPT2Tokenizer
from src.config import ProjectConfig
import matplotlib.pyplot as plt
from src.tokenization import tokenization

class TextModel():
    def __init__(self, config: ProjectConfig, tokenizer: tokenization):
        """ Initialize the model
        1. Initialize the model & variables
        2. Define
            - optimizer
                Choose adam optimizer.
                Control the clipnorm parameters to clip the gradient.
            - loss -> Using SparseCategoricalCrossentropy
                Since there will be only one attr in the dataset,
                use sparse categorial crossentropy.
                Set from_logits to True may improve numerical stablility.
            - metric
        3. Compile into the model
        """
        # Initialize Model
        gpt_config = GPT2Config(
            architectures=["TFGPT2LMHeadModel"],
            model_type="TFGPT2LMHeadModel",
            vocab_size=tokenizer.vocab_size,
            bos_token_id=tokenizer.bos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
        # Initialize variables
        self.config = config
        self.model = TFGPT2LMHeadModel(config=gpt_config)
        self.tokenizer = tokenizer
        self.history : tf.keras.callbacks.History
        self.batch_end_loss = list()
        # Define
        self.optimizer = tf.keras.optimizers.Adam(learning_rate=5e-5, epsilon=1e-08, clipnorm=1.0)
        self.loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        self.metric = tf.keras.metrics.SparseCategoricalAccuracy('accuracy')
        # Compiling the model
        self.model.compile(
            optimizer=self.optimizer, 
            loss=[self.loss, *[None] * self.model.config.n_layer], 
            metrics=[self.metric]
        )

    def train(self, dataset: tf.data.Dataset):
        """ Train model & Save it to the path
        1. Set callback function to store model per epoch
            - inherited from  tf.keras.callbacks.Callback
            1. Override to save model in config.model_pos
            2. Save batch loss end of trainning a batch
            3. Supress the model fit output and customized with self callback function
        2. Store history and visualize it
        """
        # Pass parameters for callback functions
        batch_end_loss = list()
        config = self.config
        # Callback functions
        class SaveModelCallback (tf.keras.callbacks.Callback):
            interval = 5
            def on_epoch_end(self, epoch, logs=None):
                if epoch % 5 == 0 or epoch == 1:
                    self.model.save_pretrained(f"{config.model_pos}-{epoch+1}")
        class SaveBatchLossCallback(tf.keras.callbacks.Callback):
            def on_train_batch_end(self, batch, logs=None):
                batch_end_loss.append(logs['loss'])
        class ShowLossCallback(tf.keras.callbacks.Callback):
            interval = 100
            counter = 0
            epoch = 0
            # begin of one epoch
            def on_epoch_begin(self, epoch, logs=None):
                self.epoch = epoch
                self.counter = 0
            def on_train_batch_end(self, batch, logs=None):
                if self.counter % self.interval == 0:
                    print(f"Epoch: {self.epoch+1} \n\tBatch: {self.counter}/{dataset.__len__()} \n\tLoss: {str(logs['loss'])}")
                self.counter += 1
        self.batch_end_loss = batch_end_loss
        # Train Model and Store into History Object
        self.history = self.model.fit(
            dataset, 
            verbose=0,
            epochs=self.config.epoch_times,
            callbacks=[
                SaveModelCallback(),
                SaveBatchLossCallback(),
                ShowLossCallback()
            ]
        )
        return self.model

    def visualize(self):
        """ Visualize 
        1. Using stored history to visualize trainning history
        2. Visualize the accuracy
        3. Visualize the loss
        """
        # Per epoch
        plt.figure(figsize=(10, 5))
        plt.plot(self.history.history['loss'])
        plt.legend(['train'], loc='upper left')
        plt.title('Loss (Per epoch)')
        plt.xlabel('epoch')
        plt.ylabel('loss')
        plt.show()

        # Per batch
        plt.figure(figsize=(10, 5))
        plt.plot(self.batch_end_loss)
        plt.legend(['train'], loc='upper left')
        plt.title('Loss (Per batch)')
        plt.xlabel('batch')
        plt.ylabel('loss')
        plt.show()

    def trainning_output(self):
        """ output
        - This is a test function
        - Output the result, metadata of the model trainning
        """
        # Local variable
        per_epoch_loss = self.history.history['loss']
        # GPT model config
        print(f"## GPT Mode Config     ##")
        print(f"{self.model.config}")
        # Per Epoch and loss
        print(f"## Loss (Per Epoch)    ##")
        for idx, loss in enumerate(per_epoch_loss):
            print(f"\tEpoch {idx} -> Loss: {loss}")
        # Batch loss for every 1000 batch number
        print(f"## Loss (Per Batch)    ##")
        for idx, loss in enumerate(self.batch_end_loss):
            if idx % 1000 == 0:
                print(f"\tBatch {idx} -> Loss: {loss}")
        # Loss Information
        print(f"## Loss Information    ##")
        print(f"Avg. loss: {sum(per_epoch_loss) / len(per_epoch_loss)} \n\t\
        Max Loss: {max(per_epoch_loss)} \n\tMin Loss: {min(per_epoch_loss)}")