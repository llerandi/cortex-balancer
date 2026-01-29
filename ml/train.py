import os
import requests
import numpy as np

import tensorflow as tf
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step as ts
from tf_agents.networks import q_network
from tf_agents.agents.dqn import dqn_agent
from tf_agents.replay_buffers import reverb_replay_buffer, reverb_utils
from tf_agents.policies import random_py_policy
from tf_agents.utils import common

# --- CONFIGURATION ---
# The URL of our Environment API (obtained from an environment variable), easily switch between local and production
ENVIRONMENT_API_URL = os.environ.get("ENV_API_URL", "http://localhost:8080/api/v1/environment")

# Training parameters
NUM_WORKERS = 3
NUM_ITERATIONS = 5000  # Number of times the agent will train
COLLECT_STEPS_PER_ITERATION = 1
REPLAY_BUFFER_MAX_LENGTH = 100000
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
LOG_INTERVAL = 200

# --- 1. BRIDGE WITH JAVA ---
# This class makes the REST API look like a standard RL environment
class LoadBalancerEnv(py_environment.PyEnvironment):
    def __init__(self):
        super().__init__()
        # Specify the action: a single integer (0, 1, or 2)
        self._action_spec = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int32, minimum=0, maximum=NUM_WORKERS - 1, name='action')
        # Specify the observation (state): an array of floats (the load of each worker)
        self._observation_spec = array_spec.ArraySpec(
            shape=(NUM_WORKERS,), dtype=np.float32, name='observation')

    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec

    def _reset(self):
        """Call the /reset endpoint (Java API)."""
        print("-> Reiniciando entorno...")
        response = requests.get(f"{ENVIRONMENT_API_URL}/reset")
        response.raise_for_status() # Throw an error if the request fails
        data = response.json()
        initial_state = np.array(data['initialState'], dtype=np.float32)
        return ts.restart(initial_state)

    def _step(self, action):
        """Call the /step endpoint (Java API) with the chosen action."""
        # The 'action' comes as a numpy array, casted as int
        action_int = int(action)
        
        response = requests.post(f"{ENVIRONMENT_API_URL}/step", json={'action': action_int})
        response.raise_for_status()
        
        data = response.json()
        new_state = np.array(data['newState'], dtype=np.float32)
        reward = np.float32(data['reward'])
        done = bool(data['done'])

        if done:
            return ts.termination(new_state, reward)
        else:
            return ts.transition(new_state, reward=reward, discount=1.0)

# --- MAIN TRAINING LOGIC ---
if __name__ == "__main__":
    print("--- Starting the agent training process ---")
    print(f"Environment configured to point to: {ENVIRONMENT_API_URL}")

    # Instantiate the training and evaluation environment.
    train_py_env = LoadBalancerEnv()
    
    # --- 2. NEURAL NETWORK ---
    # A simple neural network with two hidden layers of 100 neurons
    fc_layer_params = (100, 50)
    q_net = q_network.QNetwork(
        train_py_env.observation_spec(),
        train_py_env.action_spec(),
        fc_layer_params=fc_layer_params)

    # --- 3. THE AGENT ---
    optimizer = tf.compat.v1.train.AdamOptimizer(learning_rate=LEARNING_RATE)
    train_step_counter = tf.Variable(0)

    agent = dqn_agent.DqnAgent(
        train_py_env.time_step_spec(),
        train_py_env.action_spec(),
        q_network=q_net,
        optimizer=optimizer,
        td_errors_loss_fn=common.element_wise_squared_loss,
        train_step_counter=train_step_counter)
    
    agent.initialize()
    print("DQN agent initialised.")

    # --- 4. TRAINING LOOP ---
    # The Replay Buffer is the agent's memory (it stores experiences so that it can learn from them)
    replay_buffer = reverb_replay_buffer.ReverbReplayBuffer(
        agent.collect_data_spec,
        table_name="uniform_table",
        sequence_length=2,
        local_server=reverb.Server([reverb.Table(
            name="uniform_table",
            max_size=REPLAY_BUFFER_MAX_LENGTH,
            sampler=reverb.selectors.Uniform(),
            remover=reverb.selectors.Fifo(),
            rate_limiter=reverb.rate_limiters.MinSize(1))]))

    # Function to collect an experience step and add it to memory
    def collect_step(environment, policy, buffer):
        time_step = environment.current_time_step()
        action_step = policy.action(time_step)
        next_time_step = environment.step(action_step.action)
        traj = tf_agents.trajectories.from_transition(time_step, action_step, next_time_step)
        buffer.add_batch(traj)

    # Fill the memory with some random experiences at the beginning
    print("Gathering initial random experiences...")
    random_policy = random_py_policy.RandomPyPolicy(train_py_env.time_step_spec(), train_py_env.action_spec())
    for _ in range(100): # Collect 100 random steps.
        collect_step(train_py_env, random_policy, replay_buffer.py_client)

    # Convert the memory into a TensorFlow dataset for training
    dataset = replay_buffer.as_dataset(
        num_parallel_calls=3, 
        sample_batch_size=BATCH_SIZE, 
        num_steps=2).prefetch(3)
    iterator = iter(dataset)

    # Main training loop
    agent.train = common.function(agent.train)
    agent.train_step_counter.assign(0)
    
    print("--- Training begins ---")
    for i in range(NUM_ITERATIONS):
        # Gain experience using the agent's current policy
        collect_step(train_py_env, agent.collect_policy, replay_buffer.py_client)

        # Train the agent with a batch of memory experiences
        experience, unused_info = next(iterator)
        train_loss = agent.train(experience).loss

        step = agent.train_step_counter.numpy()

        if step % LOG_INTERVAL == 0:
            print(f'step = {step}: loss = {train_loss}')

    print("--- Training completed ---")

    # TODO:
    # 1. Save the trained policy
    # 2. Deployment to Vertex AI Endpoints