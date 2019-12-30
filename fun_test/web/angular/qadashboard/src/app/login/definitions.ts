import {Api} from "../lib/api";

export class User {
  id: number;
  is_authenticated: boolean;
  first_name: string;
  last_name: string;
  email: string;

  constructor(props) {
    Object.assign(this, props);
  }
}

export class UserProfile extends Api {
  classType = UserProfile;
  url = "/api/v1/user_profiles";
  id: number;
  is_anonymous: boolean = false;
  user: User = null;
  serialize() {
    return {};
  }

  deserializationHooks = {user: function(data)  {
      return new User(data);
    }
  };
}
