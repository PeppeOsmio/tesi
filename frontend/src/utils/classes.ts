export class User {
    id: string;
    username: string;
    constructor(id: string, username: string) {
        this.id = id;
        this.username = username;
    }
}

// Define a type for the context
export interface AuthContextType {
    currentUser: User | null;
    setCurrentUser: React.Dispatch<React.SetStateAction<User | null>>;
}
