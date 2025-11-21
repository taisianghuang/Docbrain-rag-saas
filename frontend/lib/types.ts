export type WidgetConfig = {
  title: string;
  primaryColor: string;
  welcomeMessage: string;
};

export type ChatMessage = {
  role: 'user' | 'model';
  text: string;
  timestamp: number;
};
