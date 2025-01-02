"""
A Minimal Deep Q-Learning Implementation (minDQN)
"""

import gym
import tensorflow as tf
import numpy as np
from tensorflow import keras

from collections import deque
import time
import random

import matplotlib.pyplot as plt  # Library for plotting

RANDOM_SEED = 5
tf.random.set_seed(RANDOM_SEED)

env = gym.make('CartPole-v1')
np.random.seed(RANDOM_SEED)

print("Action Space: {}".format(env.action_space))
print("State space: {}".format(env.observation_space))

# An episode a full game
train_episodes = 300
test_episodes = 100

def agent(state_shape, action_shape):
    """ The agent maps X-states to Y-actions
    e.g. The neural network output is [.1, .7, .1, .3]
    The highest value 0.7 is the Q-Value.
    The index of the highest action (0.7) is action #1.
    """
    learning_rate = 0.001
    init = tf.keras.initializers.HeUniform()
    model = keras.Sequential()
    model.add(keras.layers.Dense(24, input_shape=state_shape, activation='relu', kernel_initializer=init))
    model.add(keras.layers.Dense(12, activation='relu', kernel_initializer=init))
    model.add(keras.layers.Dense(action_shape, activation='linear', kernel_initializer=init))
    model.compile(loss=tf.keras.losses.Huber(), optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate), metrics=['accuracy'])
    return model

def get_qs(model, state, step):
    return model.predict(state.reshape([1, state.shape[0]]))[0]

def train(env, replay_memory, model, target_model, done):
    learning_rate = 0.7 # Learning rate
    discount_factor = 0.618

    MIN_REPLAY_SIZE = 1000
    if len(replay_memory) < MIN_REPLAY_SIZE:
        return

    batch_size = 64 * 2
    print(f"len(replay_memory): {len(replay_memory)}")
    print(f"replay_memory: {replay_memory[0]}")
    mini_batch = random.sample(replay_memory, batch_size)
    # print(f"mini_batch: {mini_batch}")
    print(f"len of mini_batch: {len(mini_batch)}")
    current_states = np.array([transition[0] for transition in mini_batch])
    # print(f"current_states: {current_states}")
    print(f"len of current_states: {len(current_states)}")
    current_qs_list = model.predict(current_states)
    # print(f"current_qs_list: {current_qs_list}")
    print(f"len of current_qs_list: {len(current_qs_list)}")
    new_current_states = np.array([transition[3] for transition in mini_batch])
    # print(f"new_current_states: {new_current_states}")
    print(f"len of new_current_states: {len(new_current_states)}")
    future_qs_list = target_model.predict(new_current_states)
    # print(f"future_qs_list: {future_qs_list}")
    print(f"len of future_qs_list: {len(future_qs_list)}")

    X = []
    Y = []
    for index, (observation, action, reward, new_observation, done) in enumerate(mini_batch):
        if not done:
            max_future_q = reward + discount_factor * np.max(future_qs_list[index])
        else:
            max_future_q = reward

        current_qs = current_qs_list[index]
        current_qs[action] = (1 - learning_rate) * current_qs[action] + learning_rate * max_future_q

        X.append(observation)
        Y.append(current_qs)
    model.fit(np.array(X), np.array(Y), batch_size=batch_size, verbose=0, shuffle=True)
    while True:
        pass

    exit(1)


    
def main():
    epsilon = 1 # Epsilon-greedy algorithm in initialized at 1 meaning every step is random at the start
    max_epsilon = 1 # You can't explore more than 100% of the time
    min_epsilon = 0.01 # At a minimum, we'll always explore 1% of the time
    decay = 0.01

    # 1. Initialize the Target and Main models
    # Main Model (updated every 4 steps)
    model = agent(env.observation_space.shape, env.action_space.n)
    # Target Model (updated every 100 steps)
    target_model = agent(env.observation_space.shape, env.action_space.n)
    target_model.set_weights(model.get_weights())

    replay_memory = deque(maxlen=50_000)

    rewards = []

    steps_to_update_target_model = 0

    for episode in range(train_episodes):
        total_training_rewards = 0
        observation = env.reset(seed=RANDOM_SEED)[0]
        done = False

        print(f"\n--- Episode {episode + 1}/{train_episodes} ---")
        print(f"Initial Observation: {observation}")

        while not done:
            steps_to_update_target_model += 1
            
            # Render environment (optional, can slow down training)
            if True:
                env.render()

            random_number = np.random.rand()
            print(f"\nStep {steps_to_update_target_model}")
            print(f"Random number for epsilon-greedy decision: {random_number}")
            print(f"Current Epsilon: {epsilon}")

            # Epsilon-greedy action selection
            if random_number <= epsilon:
                action = env.action_space.sample()
                print(f"Action taken: {action} (random - explore)")
            else:
                encoded = observation
                encoded_reshaped = np.reshape(encoded, [1, env.observation_space.shape[0]])
                predicted = model.predict(encoded_reshaped).flatten()
                action = np.argmax(predicted)
                print(f"Predicted Q-values: {predicted}")
                print(f"Action taken: {action} (exploit)")

            new_observation, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            print(f"New Observation: {new_observation}")
            print(f"Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}, Done: {done}")

            # Append experience to replay memory
            replay_memory.append([observation, action, reward, new_observation, done])
            print(f"Replay memory size: {len(replay_memory)}")

            # Train the network every 4 steps or when done
            if steps_to_update_target_model % 4 == 0 or done:
                print("Training the model...")
                print(f"env: {env}")
                print(f"replay_memory: {replay_memory}")
                print(f"model: {model}")
                print(f"target_model: {target_model}")
                print(f"done: {done}")
                train(env, replay_memory, model, target_model, done)

            observation = new_observation
            total_training_rewards += reward

            if done:
                print(f"Total training rewards for episode {episode}: {total_training_rewards}")
                rewards.append(total_training_rewards)

                # Update target network
                if steps_to_update_target_model >= 100:
                    print('Updating target network weights...')
                    target_model.set_weights(model.get_weights())
                    steps_to_update_target_model = 0
                break

        # Update epsilon (decay)
        epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(-decay * episode)
        print(f"Updated Epsilon: {epsilon}")
        # break

    env.close()

    plt.figure(figsize=(10,6))  # Set the figure size
    plt.plot(rewards, label='Q-learning Train')  # Plot Q-learning training rewards
    plt.xlabel('Episode')  # Label x-axis
    plt.ylabel('Total Reward')  # Label y-axis
    plt.title('Q-Learning (Episode vs Rewards)')
    plt.legend()  # Display legend
    plt.show()  # Show the plot

if __name__ == '__main__':
    main()