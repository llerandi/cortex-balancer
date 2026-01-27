package com.example.cortexbalancer.environment_api;

import java.util.List;

// Java 'records' to create immutable data classes
public class ApiDto {

    // The JSON that the AI will send here when it wants to execute an action (e.g., { "action": 2 })
    public record ActionRequest(int action) {}

    /**
     * The response that will be sent to the AI after each step
     * Contains the new system status, reward obtained, and whether the 'game' has ended
     */
    public record StepResponse(List<Double> newState, double reward, boolean done) {}

    /**
     * The response that will be sent to the AI when the AI requests to restart the environment
     * Contains only the initial state of the system
     */
    public record ResetResponse(List<Double> initialState) {}
    
}