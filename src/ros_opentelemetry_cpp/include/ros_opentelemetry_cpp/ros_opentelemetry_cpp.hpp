#pragma once
#include <map>
#include <memory>
#include <opentelemetry/context/context.h>
#include <opentelemetry/context/propagation/text_map_propagator.h>
#include <opentelemetry/context/runtime_context.h>
#include <opentelemetry/exporters/otlp/otlp_grpc_exporter_factory.h>
#include <opentelemetry/exporters/otlp/otlp_grpc_exporter_options.h>
#include <opentelemetry/nostd/span.h>
#include <opentelemetry/sdk/resource/resource.h>
#include <opentelemetry/sdk/resource/semantic_conventions.h>
#include <opentelemetry/sdk/trace/batch_span_processor.h>
#include <opentelemetry/sdk/trace/exporter.h>
#include <opentelemetry/sdk/trace/tracer_provider_factory.h>
#include <opentelemetry/trace/context.h>
#include <opentelemetry/trace/propagation/http_trace_context.h>
#include <opentelemetry/trace/provider.h>
#include <opentelemetry/trace/semantic_conventions.h>
#include <opentelemetry/trace/span.h>
#include <opentelemetry/trace/trace_id.h>
#include <opentelemetry/trace/tracer.h>
#include <optional>
#include <rclcpp/rclcpp.hpp>
#include <ros_opentelemetry_interfaces/msg/key_value.hpp>
#include <ros_opentelemetry_interfaces/msg/trace_metadata.hpp>
#include <string>
#include <utility>

namespace ros_opentelemetry_cpp {

namespace otel = opentelemetry;
namespace sdk = opentelemetry::sdk;
namespace trace = opentelemetry::trace;
namespace ctx = opentelemetry::context;
namespace ctxprop = opentelemetry::context::propagation;
namespace traceprop = opentelemetry::trace::propagation;

class MapCarrier : public ctxprop::TextMapCarrier {
public:
  explicit MapCarrier(std::map<std::string, std::string> &map_carrier)
      : map_(map_carrier) {}
  [[nodiscard]] auto Get(otel::nostd::string_view key) const noexcept
      -> otel::nostd::string_view override {
    auto iter = map_.find(std::string(key));
    if (iter == map_.end()) {
      return {};
    }
    return iter->second;
  }
  void Set(otel::nostd::string_view key,
           otel::nostd::string_view value) noexcept override {
    map_[std::string(key)] = std::string(value);
  }

private:
  std::map<std::string, std::string> &map_;
};

inline auto make_resource(const std::string &service_name)
    -> sdk::resource::Resource {
  using namespace sdk::resource;
  return Resource::Create({{SemanticConventions::kServiceName, service_name}});
}

inline void
setup_tracer(const std::string &service_name,
             std::optional<std::string> otlp_grpc_endpoint = std::nullopt) {
  opentelemetry::exporter::otlp::OtlpGrpcExporterOptions opts;
  if (otlp_grpc_endpoint && !otlp_grpc_endpoint->empty()) {
    opts.endpoint = *otlp_grpc_endpoint;
  }
  auto exporter =
      opentelemetry::exporter::otlp::OtlpGrpcExporterFactory::Create(opts);
  sdk::trace::BatchSpanProcessorOptions bs_opts;
  auto processor = std::unique_ptr<sdk::trace::SpanProcessor>(
      new sdk::trace::BatchSpanProcessor(std::move(exporter), bs_opts));
  auto provider_unique = sdk::trace::TracerProviderFactory::Create(
      std::move(processor), make_resource(service_name));
  std::shared_ptr<trace::TracerProvider> std_provider(
      std::move(provider_unique));
  otel::nostd::shared_ptr<trace::TracerProvider> provider(std_provider);
  trace::Provider::SetTracerProvider(provider);
}

inline auto inject_trace_context()
    -> ros_opentelemetry_interfaces::msg::TraceMetadata {
  std::map<std::string, std::string> carrier;
  MapCarrier car(carrier);
  static auto propagator = otel::nostd::shared_ptr<ctxprop::TextMapPropagator>(
      new traceprop::HttpTraceContext());
  propagator->Inject(car, ctx::Context{});
  ros_opentelemetry_interfaces::msg::TraceMetadata msg;
  msg.context.reserve(carrier.size());
  for (auto &key_val : carrier) {
    ros_opentelemetry_interfaces::msg::KeyValue pair;
    pair.key = key_val.first;
    pair.value = key_val.second;
    msg.context.push_back(std::move(pair));
  }
  return msg;
}

inline auto update_trace_context(
    const ros_opentelemetry_interfaces::msg::TraceMetadata &trace_context,
    const std::map<std::string, std::string> &data)
    -> ros_opentelemetry_interfaces::msg::TraceMetadata {
  ros_opentelemetry_interfaces::msg::TraceMetadata out;
  out.context = trace_context.context;
  out.context.reserve(out.context.size() + data.size());
  for (const auto &key_val : data) {
    ros_opentelemetry_interfaces::msg::KeyValue pair;
    pair.key = key_val.first;
    pair.value = key_val.second;
    out.context.push_back(std::move(pair));
  }
  return out;
}

inline auto extract_trace_context(
    const ros_opentelemetry_interfaces::msg::TraceMetadata *trace_context)
    -> ctx::Context {
  if (trace_context == nullptr || trace_context->context.empty()) {

    return ctx::Context{};
  }
  std::map<std::string, std::string> carrier_map;
  for (const auto &key_val : trace_context->context) {
    carrier_map.emplace(key_val.key, key_val.value);
  }
  MapCarrier car(carrier_map);
  static auto propagator = otel::nostd::shared_ptr<ctxprop::TextMapPropagator>(
      new traceprop::HttpTraceContext());
  auto context = ctx::Context{};
  return propagator->Extract(car, context);
}

inline auto trace_prefix() -> std::string {

  auto current_span = trace::GetSpan(ctx::RuntimeContext::GetCurrent());
  if (!current_span) {
    return std::string{};
  }

  auto span_context = current_span->GetContext();
  if (!span_context.IsValid()) {
    return std::string{};
  }
  std::array<char, 32> trace_id = {0};
  std::array<char, 16> span_id = {0};

  span_context.trace_id().ToLowerBase16(trace_id);
  span_context.span_id().ToLowerBase16(span_id);
  return "[trace_id=" + std::string(trace_id.data(), 32) +
         " span_id=" + std::string(span_id.data(), 16) + "] ";
}

// Generic helper that prepends the prefix to the format string and forwards
// args.
template <typename... Args>
inline void info_traced(const rclcpp::Logger &logger, const char *fmt,
                        Args &&...args) {
  const std::string composed = trace_prefix() + fmt;
  RCLCPP_INFO(logger, composed.c_str(), std::forward<Args>(args)...);
}

template <typename... Args>
inline void debug_traced(const rclcpp::Logger &logger, const char *fmt,
                         Args &&...args) {
  const std::string composed = trace_prefix() + fmt;
  RCLCPP_DEBUG(logger, composed.c_str(), std::forward<Args>(args)...);
}

template <typename... Args>
inline void warn_traced(const rclcpp::Logger &logger, const char *fmt,
                        Args &&...args) {
  const std::string composed = trace_prefix() + fmt;
  RCLCPP_WARN(logger, composed.c_str(), std::forward<Args>(args)...);
}

template <typename... Args>
inline void error_traced(const rclcpp::Logger &logger, const char *fmt,
                         Args &&...args) {
  const std::string composed = trace_prefix() + fmt;
  RCLCPP_ERROR(logger, composed.c_str(), std::forward<Args>(args)...);
}

template <typename... Args>
inline void fatal_traced(const rclcpp::Logger &logger, const char *fmt,
                         Args &&...args) {
  const std::string composed = trace_prefix() + fmt;
  RCLCPP_FATAL(logger, composed.c_str(), std::forward<Args>(args)...);
}

#define RCLCPP_INFO_TRACED(logger, fmt, ...)                                   \
  ::ros_opentelemetry_cpp::info_traced(logger, fmt, ##__VA_ARGS__)
#define RCLCPP_DEBUG_TRACED(logger, fmt, ...)                                  \
  ::ros_opentelemetry_cpp::debug_traced(logger, fmt, ##__VA_ARGS__)
#define RCLCPP_WARN_TRACED(logger, fmt, ...)                                   \
  ::ros_opentelemetry_cpp::warn_traced(logger, fmt, ##__VA_ARGS__)
#define RCLCPP_ERROR_TRACED(logger, fmt, ...)                                  \
  ::ros_opentelemetry_cpp::error_traced(logger, fmt, ##__VA_ARGS__)
#define RCLCPP_FATAL_TRACED(logger, fmt, ...)                                  \
  ::ros_opentelemetry_cpp::fatal_traced(logger, fmt, ##__VA_ARGS__)

} // namespace ros_opentelemetry_cpp
