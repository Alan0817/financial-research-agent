export class DemoApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DemoApiError";
  }
}
