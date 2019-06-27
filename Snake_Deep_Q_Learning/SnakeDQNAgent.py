#          ____              _          ____   ___  _   _    _                    _
#         / ___| _ __   __ _| | _____  |  _ \ / _ \| \ | |  / \   __ _  ___ _ __ | |_
#         \___ \| '_ \ / _` | |/ / _ \ | | | | | | |  \| | / _ \ / _` |/ _ \ '_ \| __|
#          ___) | | | | (_| |   <  __/ | |_| | |_| | |\  |/ ___ \ (_| |  __/ | | | |_
#         |____/|_| |_|\__,_|_|\_\___| |____/ \__\_\_| \_/_/   \_\__, |\___|_| |_|\__|
#                                                                |___/
import numpy as np
from tensorflow.keras import models, layers, optimizers
from tensorflow.keras.models import clone_model
from collections import deque


class DQNAgent():

    def __init__(self, state_size, actions):
        self.state_size = state_size
        self.actions = actions
        self.action_size = len(self.actions)   # ['up', 'right', 'down', 'left']
        self.actions_encoded = np.identity(self.action_size)
        # Agent hyper-parameters
        self.memory_size = 1000
        self.memory = deque(maxlen=self.memory_size)
        self.discount_rate = 0.5             # gamma
        self.exploration_rate = 1              # epsilon, will decay with time
        self.min_exploration_rate = 0.1
        self.exploration_rate_decay = 0.9995
        self.learning_rate = 0.01              # alpha
        self.counter_to_update_target_nn = 0
        self.max_counter_to_update_target_nn = 200
        self.batch_size = 2
        # Related with Neural network
        self._build_models()
        self.epochs = 1

    def _build_models(self):
        # Neural Net for Deep-Q learning Model
        self.policy_nn = models.Sequential()
        self.policy_nn.add(layers.Dense(64, activation='relu', input_shape=(self.state_size,)))
        self.policy_nn.add(layers.Dense(32, activation='relu'))
        self.policy_nn.add(layers.Dense(self.action_size))
        self.policy_nn.compile(loss='mse', optimizer=optimizers.RMSprop(lr=self.learning_rate))
        self.target_nn = clone_model(self.policy_nn)

    def enconde_action(self, action_name):
        action_idx = self.actions.index(action_name)
        return self.actions_encoded[action_idx]

    def remember(self, state, action_name, reward, new_state, dead):
        self.memory.append((state, self.enconde_action(action_name), reward, new_state, dead))
        return True

    def act(self, state):
        if np.random.rand() <= self.exploration_rate:
            random_action = self.actions[np.random.randint(0, self.action_size)]
            return random_action
        q_values = self.policy_nn.predict(state.reshape(1, self.state_size))
        best_action = self.actions[np.argmax(q_values)]
        return best_action

    def _unpack_history(self):
        # Initialize vectors
        states = np.ndarray((self.batch_size, self.state_size))
        actions = np.ndarray((self.batch_size, self.action_size))
        new_states = np.ndarray((self.batch_size, self.state_size))
        rewards = np.ndarray((self.batch_size, 1))
        deads = np.ndarray((self.batch_size, 1))
        # Iterate over a history batch
        memory_indexes = range(len(self.memory))
        random_indexes = np.random.choice(memory_indexes, size=self.batch_size)
        for idx, random_idx in enumerate(random_indexes):
            state, action, reward, new_state, dead = self.memory[random_idx]
            states[idx] = state
            actions[idx] = action
            new_states[idx] = state
            rewards[idx] = reward
            deads[idx] = dead
        return states, actions, rewards, new_states, deads

    def replay(self):
        if len(self.memory) > self.batch_size:
            # ------------
            states, actions, rewards, new_states, deads = self._unpack_history()
            targets = rewards * actions + deads * self.discount_rate * self.target_nn.predict(new_states) + self.policy_nn.predict(states)
            self.policy_nn.fit(x=states, y=targets, epochs=self.epochs, verbose=0)
            # ------------
            # Iterate over a history batch
            #  memory_indexes = range(len(self.memory))
            #  random_indexes = np.random.choice(memory_indexes, size=self.batch_size)
            #  for idx, random_idx in enumerate(random_indexes):
            #      state, action, reward, new_state, dead = self.memory[random_idx]
            #      target = reward * action + dead * self.discount_rate * np.amax(self.target_nn.predict(new_state.reshape(1, self.state_size)), axis=1)
            #      self.policy_nn.fit(state.reshape(1, self.state_size), target.reshape(1, self.action_size), verbose=0, epochs=self.epochs)
            # ------------
            # Predict all the possibilities
            #  targets = rewards * actions + deads * self.discount_rate * self.target_nn.predict(new_states)
            #    learned_value = rewards * actions + self.discount_rate * self.target_nn.predict(new_states)
            #    target = (1 - self.alpha) * (self.policy_nn.predict(states)) + (self.alpha) * learned_value
            # target_predictions[:, np.argmax(actions, axis=1)] = target_values    # can be done this without a loop?
            # target_prediction[0, np.argmax(action)] = target_value
            # self.policy_nn.fit(states, targets, epochs=self.epochs, verbose=0)
            # Update exploration rate
            if self.exploration_rate > self.min_exploration_rate:
                self.exploration_rate *= self.exploration_rate_decay
            # update target policy
            if self.counter_to_update_target_nn >= self.max_counter_to_update_target_nn:
                self.counter_to_update_target_nn = 0
                self.target_nn = clone_model(self.policy_nn)
            else:
                self.counter_to_update_target_nn += 1
