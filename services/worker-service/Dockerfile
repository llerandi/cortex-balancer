# --- 1. Build stage ---
## Use an official image containing Maven and a version of Java (Temurin 21)
## To refer to it later, name it 'builder'
FROM maven:3.9-eclipse-temurin-21 AS builder

# Set the working directory inside the container
WORKDIR /app

## First, copy the 'pom.xml' (cache optimisation)
## If dependencies do not change, Docker will not download them again in future builds
COPY pom.xml .
RUN mvn dependency:go-offline

## Copy the rest of the source code for our application
COPY src ./src

## Execute the Maven command to compile the project and create the JAR file
## Use -DskipTests to avoid running tests during image construction
RUN mvn clean package -DskipTests


# --- 2. Runtime stage ---
## Start with a new, very lightweight base image ('-slim') that only contains the JRE (Java Runtime Environment)
FROM openjdk:21-slim

## Set up the working directory
WORKDIR /app

## ONLY copy the compiled JAR file from the 'builder' phase (this is what makes the final image so small)
COPY --from=builder /app/target/*.jar app.jar

## Expose port 8080 (default port for Spring Boot)
EXPOSE 8080

## The command to be executed when the container starts (simply launch the Java application)
ENTRYPOINT ["java", "-jar", "app.jar"]