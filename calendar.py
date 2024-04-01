import cmd
import sqlite3
from datetime import datetime

class CalendarCLI(cmd.Cmd):
    prompt = '> '
    
    def __init__(self):
        super().__init__()
        self.conn = sqlite3.connect('calendar.db')
        self.c = self.conn.cursor()
        self.intro = "Welcome to Calendar CLI. Type 'help' to see available commands."
        
        # Create tables if not exist
        self.c.execute('''CREATE TABLE IF NOT EXISTS persons
                          (id INTEGER PRIMARY KEY, name TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS rooms
                          (id INTEGER PRIMARY KEY, name TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS meetings
                          (id INTEGER PRIMARY KEY, name TEXT, start_time DATETIME, end_time DATETIME, room_id INTEGER, 
                          FOREIGN KEY (room_id) REFERENCES rooms(id))''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS attendees
                          (meeting_id INTEGER, person_id INTEGER,
                          FOREIGN KEY (meeting_id) REFERENCES meetings(id),
                          FOREIGN KEY (person_id) REFERENCES persons(id))''')
        self.conn.commit()
        
    def do_schedule(self, arg):
        "Schedule a meeting. Usage: schedule <name> <start_time> <end_time> <room_id> <attendee_ids separated by space>"
        args = arg.split()
        if len(args) < 5:
            print("Insufficient arguments.")
            return
        
        name = args[0]
        start_time = datetime.fromisoformat(args[1])
        end_time = datetime.fromisoformat(args[2])
        room_id = int(args[3])
        attendee_ids = [int(id) for id in args[4:]]
        
        collision_check = self.collision_check(start_time, end_time, room_id)
        if collision_check:
            print("Collision detected. Meeting cannot be scheduled.")
            return
        
        availability_check = self.check_availability(attendee_ids, start_time, end_time)
        if not availability_check:
            print("Some attendees are not available at that time.")
            return
        
        self.schedule_meeting(name, start_time, end_time, room_id, attendee_ids)
        print("Meeting scheduled successfully.")
    
    def collision_check(self, start_time, end_time, room_id):
        self.c.execute('''SELECT * FROM meetings 
                          WHERE room_id=? AND 
                          ((start_time BETWEEN ? AND ?) OR 
                          (end_time BETWEEN ? AND ?))''',
                        (room_id, start_time, end_time, start_time, end_time))
        return self.c.fetchone() is not None
    
    def check_availability(self, attendee_ids, start_time, end_time):
        for person_id in attendee_ids:
            self.c.execute('''SELECT * FROM attendees 
                              JOIN meetings ON attendees.meeting_id = meetings.id 
                              WHERE attendees.person_id=? AND 
                              ((meetings.start_time BETWEEN ? AND ?) OR 
                              (meetings.end_time BETWEEN ? AND ?))''',
                            (person_id, start_time, end_time, start_time, end_time))
            if self.c.fetchone() is not None:
                return False
        return True
    
    def schedule_meeting(self, name, start_time, end_time, room_id, attendee_ids):
        self.c.execute('''INSERT INTO meetings (name, start_time, end_time, room_id) VALUES (?, ?, ?, ?)''',
                       (name, start_time, end_time, room_id))
        meeting_id = self.c.lastrowid
        for person_id in attendee_ids:
            self.c.execute('''INSERT INTO attendees (meeting_id, person_id) VALUES (?, ?)''',
                           (meeting_id, person_id))
        self.conn.commit()
    
    def do_exit(self, arg):
        "Exit the program."
        print("Exiting...")
        return True

if __name__ == '__main__':
    CalendarCLI().cmdloop()
