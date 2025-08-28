export type RootStackParamList = {
  Login: undefined;
  Main: undefined;
  ConcertDetail: {
    concertKey: string;
    concert: any;
  };
  RecordingDetail: {
    identifier: string;
    recording: any;
  };
};

export type TabParamList = {
  Home: undefined;
  Search: undefined;
  Downloads: undefined;
  User: undefined;
};
