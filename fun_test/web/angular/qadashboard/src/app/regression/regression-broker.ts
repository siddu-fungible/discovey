import {MqBrokerMessage} from "../mq-broker/definitions";

class RegressionCatalogExecutionBrokerMessage implements MqBrokerMessage {
  routing_key = "RegressionCatalogExecutionBroker";
  message_type = 0;
  message = 0;
}
