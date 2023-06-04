FROM openjdk:11-jre
COPY monitor.jar /monitor/monitor.jar
EXPOSE 1400
ENTRYPOINT ["java", "-jar", "/monitor/monitor.jar"]