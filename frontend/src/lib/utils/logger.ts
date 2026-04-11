export enum LogLevel {
  DEBUG = "DEBUG",
  INFO = "INFO",
  WARN = "WARN",
  ERROR = "ERROR",
}

interface LoggerConfig {
  enableConsole: boolean;
  enableRemote: boolean;
  minLevel: LogLevel;
}

const order: Record<LogLevel, number> = {
  [LogLevel.DEBUG]: 0,
  [LogLevel.INFO]: 1,
  [LogLevel.WARN]: 2,
  [LogLevel.ERROR]: 3,
};

class Logger {
  private config: LoggerConfig;

  constructor(config: LoggerConfig) {
    this.config = config;
  }

  private shouldLog(level: LogLevel): boolean {
    return order[level] >= order[this.config.minLevel];
  }

  debug(message: string, data?: unknown) {
    if (!this.config.enableConsole || !this.shouldLog(LogLevel.DEBUG)) return;
    console.debug(`[${LogLevel.DEBUG}]`, message, data ?? "");
  }

  info(message: string, data?: unknown) {
    if (!this.config.enableConsole || !this.shouldLog(LogLevel.INFO)) return;
    console.info(`[${LogLevel.INFO}]`, message, data ?? "");
  }

  warn(message: string, data?: unknown) {
    if (!this.config.enableConsole || !this.shouldLog(LogLevel.WARN)) return;
    console.warn(`[${LogLevel.WARN}]`, message, data ?? "");
  }

  error(message: string, error?: Error) {
    if (!this.config.enableConsole || !this.shouldLog(LogLevel.ERROR)) return;
    console.error(`[${LogLevel.ERROR}]`, message, error ?? "");
  }
}

export const logger = new Logger({
  enableConsole: Boolean(import.meta.env.DEV),
  enableRemote: false,
  minLevel: LogLevel.INFO,
});
